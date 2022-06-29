// SPDX-License-Identifier: GPL-3.0-or-later

/// @title Shatter Core Version 1
/// @notice Core logic implementation of Shatter Core - Version 1
/// @author Transient Labs

pragma solidity ^0.8.9;

/*
_____/\\\\\\\\\\\____/\\\_________________________________________________________________________________        
 ___/\\\/////////\\\_\/\\\_________________________________________________________________________________       
  __\//\\\______\///__\/\\\____________________________/\\\__________/\\\___________________________________      
   ___\////\\\_________\/\\\__________/\\\\\\\\\_____/\\\\\\\\\\\__/\\\\\\\\\\\_____/\\\\\\\\___/\\/\\\\\\\__     
    ______\////\\\______\/\\\\\\\\\\__\////////\\\___\////\\\////__\////\\\////____/\\\/////\\\_\/\\\/////\\\_    
     _________\////\\\___\/\\\/////\\\___/\\\\\\\\\\_____\/\\\_________\/\\\_______/\\\\\\\\\\\__\/\\\___\///__   
      __/\\\______\//\\\__\/\\\___\/\\\__/\\\/////\\\_____\/\\\_/\\_____\/\\\_/\\__\//\\///////___\/\\\_________  
       _\///\\\\\\\\\\\/___\/\\\___\/\\\_\//\\\\\\\\/\\____\//\\\\\______\//\\\\\____\//\\\\\\\\\\_\/\\\_________ 
        ___\///////////_____\///____\///___\////////\//______\/////________\/////______\//////////__\///__________
   ___       _ __   __  ___  _ ______                 __ 
  / _ )__ __(_) /__/ / / _ \(_) _/ _/__ _______ ___  / /_
 / _  / // / / / _  / / // / / _/ _/ -_) __/ -_) _ \/ __/
/____/\_,_/_/_/\_,_/ /____/_/_//_/ \__/_/  \__/_//_/\__/                                                          
 ______                  _          __    __        __     
/_  __/______ ____  ___ (_)__ ___  / /_  / /  ___ _/ /  ___
 / / / __/ _ `/ _ \(_-</ / -_) _ \/ __/ / /__/ _ `/ _ \(_-<
/_/ /_/  \_,_/_//_/___/_/\__/_//_/\__/ /____/\_,_/_.__/___/                                                           
*/

import "chiru-labs/ERC721A-Upgradeable@4.1.0/contracts/ERC721AUpgradeable.sol";
import "Transient-Labs/tl-contract-kit@3.0.0/contracts/royalty/EIP2981AllToken.sol";
import "OpenZeppelin/openzeppelin-contracts-upgradeable@4.6.0/contracts/access/OwnableUpgradeable.sol";
import "OpenZeppelin/openzeppelin-contracts-upgradeable@4.6.0/contracts/utils/Base64Upgradeable.sol";
import "OpenZeppelin/openzeppelin-contracts-upgradeable@4.6.0/contracts/utils/StringsUpgradeable.sol";

contract ShatterCoreV1 is ERC721AUpgradeable, EIP2981AllToken, OwnableUpgradeable {
    using StringsUpgradeable for uint256;

    bool public isShattered;
    bool public isFused;
    uint256 public shatterStartIndex;
    uint256 public minShatters;
    uint256 public maxShatters;
    uint256 public shatters;
    uint256 public shatterTime;
    string private image;
    string private animationUrl;
    string private description;
    string[] private traitNames;
    string[] private traitValues;

    event Shattered(address indexed _user, uint256 indexed _numShatters, uint256 indexed _shatterTime);
    event Fused(address indexed _user, uint256 indexed _fuseTime);

    /// @notice function to initialize the contract
    /// @param _name is the name of the contract and piece
    /// @param _symbol is the symbol
    /// @param _royaltyRecipient is the royalty recipient
    /// @param _royaltyPercentage is the royalty percentage to set
    /// @param _minShatters is the minimum number of replicates
    /// @param _maxShatters is the maximum number of replicates
    /// @param _shatterTime is time after which replication can occur
    function initialize(string memory _name, string memory _symbol,
        address _royaltyRecipient, uint256 _royaltyPercentage,
        uint256 _minShatters, uint256 _maxShatters, uint256 _shatterTime)
        public initializerERC721A initializer
    {   
        __ERC721A_init(_name, _symbol);
        __Ownable_init();
        royaltyAddr = _royaltyRecipient;
        royaltyPerc = _royaltyPercentage;
        minShatters = _minShatters;
        maxShatters = _maxShatters;
        shatterTime = _shatterTime;
    }

    /// @notice function for minting the 1/1 to the owner's address
    /// @dev requires contract owner
    /// @dev sets the description, image, animation url (if exists), and traits for the piece - this cannot be changed later
    /// @dev requires that shatters is equal to 0 -> meaning no piece has been minted
    /// @dev using _mint function as owner() should always be an EOA or trusted entity
    function mint(string calldata _description, string calldata _image, string calldata _animationUrl,
        string[] memory _traitNames, string[] memory _traitValues) external onlyOwner
    {
        require(shatters == 0, "Already minted the first piece");
        require(_traitNames.length == _traitValues.length, "Array lengths must be equal");
        description = _description;
        image = _image;
        animationUrl = _animationUrl;
        traitNames = _traitNames;
        traitValues = _traitValues;
        shatters = 1;
        _mint(owner(), 1);
    }

    /// @notice function for owner of token 0 to unlock the piece and turn it into an edition
    /// @dev requires msg.sender to be the owner of token 0
    /// @dev requires a number of editions less than or equal to maxShatters or greater than or equal to minShatters
    /// @dev requires isShattered to be false
    /// @dev requires block timestamp to be greater than or equal to shatterTime
    /// @dev purposefully not letting approved addresses shatter as we want owner to be the only one to shatter the token
    /// @dev if number of editions == 1, fuse occurs at the same time
    /// @param _shatters is the total number of editions to make. Can be set between minShatters and maxShatters. This number is the total number of editions that will live on this contract
    function shatter(uint256 _shatters) external {
        require(!isShattered, "Already is shattered");
        require(msg.sender == ownerOf(0), "Caller is not owner of token 0");
        require(_shatters >= minShatters && _shatters <= maxShatters, "Cannot set number of editions above max or below the min");
        require(block.timestamp >= shatterTime, "Cannot shatter prior to shatterTime");

        isShattered = true;
        shatters = _shatters;
        if (_shatters > 1) {
            shatterStartIndex = 1;
            _burn(0);
            _mint(msg.sender, _shatters);
            emit Shattered(msg.sender, _shatters, block.timestamp);
        } else {
            isFused = true;
            emit Shattered(msg.sender, _shatters, block.timestamp);
            emit Fused(msg.sender, block.timestamp);
        }
    }

    /// @notice function to fuse editions back into a 1/1
    /// @dev requires msg.sender to own all of the editions
    /// @dev can't have already fused
    /// @dev must be shattered
    /// @dev purposefully not letting approved addresses fuse as we want the owner to have only control over fusing
    function fuse() external {
        require(!isFused, "Already is fused");
        require(isShattered, "Can't fuse if not already shattered");
        for (uint256 i = shatterStartIndex; i < shatterStartIndex + shatters; i++) {
            require(msg.sender == ownerOf(i), "Msg sender must own all editions");
            _burn(i);
        }
        isFused = true;
        shatters = 1;
        _mint(msg.sender, 1);

        emit Fused(msg.sender, block.timestamp);
    }

    /// @notice function to override tokenURI
    function tokenURI(uint256 tokenId) override public view returns(string memory) {
        require(_exists(tokenId), "URI query for nonexistent token");
        string memory name = name();
        string memory attr = "[";
        string memory shatterStr = "No";
        string memory fuseStr = "No";
        for (uint256 i; i < traitNames.length; i++) {
            attr = string(abi.encodePacked(attr, '{"trait_type": "', traitNames[i], '", "value": "', traitValues[i], '"},'));
        }
        if (shatters > 1) {
            shatterStr = "Yes";
            name = string(abi.encodePacked(name, ' #', tokenId.toString(), '/', shatters.toString()));
            attr = string(abi.encodePacked(attr, '{"trait_type": "Edition", "value": "', tokenId.toString(), '"},{"trait_type": "Shattered", "value": "', shatterStr, '"},{"trait_type": "Fused", "value": "', fuseStr, '"}'));
        } else {
            if (isShattered) {
                shatterStr = "Yes";
            }
            if (isFused) {
                fuseStr = "Yes";
            }
            attr = string(abi.encodePacked(attr, '{"trait_type": "Shattered", "value": "', shatterStr, '"},{"trait_type": "Fused", "value": "', fuseStr, '"}'));
        }
        attr = string(abi.encodePacked(attr, "]"));
        if (bytes(animationUrl).length == 0) {
            return string(
                abi.encodePacked(
                    "data:application/json;base64,",
                    Base64Upgradeable.encode(bytes(abi.encodePacked(
                        '{"name": "', name, '",',
                        '"description": "', description, '",',
                        '"attributes": ', attr, ',',
                        '"image": "', image, '"}'
                    )))
                )
            );
        } else {
            return string(
                abi.encodePacked(
                    "data:application/json;base64,",
                    Base64Upgradeable.encode(bytes(abi.encodePacked(
                        '{"name": "', name, '",',
                        '"description": "', description, '",',
                        '"attributes": ', attr, ',',
                        '"image": "', image, '",',
                        '"animation_url": "', animationUrl, '"}'
                    )))
                )
            );
        }
    }

    /// @notice overrides supportsInterface function
    /// @param interfaceId is supplied from anyone/contract calling this function, as defined in ERC 165
    /// @return boolean saying if this contract supports the interface or not
    function supportsInterface(bytes4 interfaceId) public view override(ERC721AUpgradeable, EIP2981AllToken) returns (bool) {
        return ERC721AUpgradeable.supportsInterface(interfaceId) || EIP2981AllToken.supportsInterface(interfaceId);
    }
}