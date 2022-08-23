// SPDX-License-Identifier: Apache-2.0

/// @title ShatterV1
/// @notice Shatter V1 implementation. 1/1 turns into carbon-copy editions upon Shatter.
/// @author transientlabs.xyz

pragma solidity 0.8.14;

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

import "./ERC721S.sol";
import "Transient-Labs/tl-contract-kit@6.1.0/contracts/royalty/EIP2981AllToken.sol";
import "OpenZeppelin/openzeppelin-contracts@4.7.0/contracts/access/Ownable.sol";

contract ShatterV1 is ERC721S, EIP2981AllToken, Ownable {
    using Strings for uint256;

    bool public isShattered;
    bool public isFused;
    uint256 public minShatters;
    uint256 public maxShatters;
    uint256 public shatters;
    uint256 public shatterTime;
    address public adminAddress;
    address private _shatterAddress;
    string private _baseUri;

    event Shattered(address indexed user, uint256 indexed numShatters, uint256 indexed shatteredTime);
    event Fused(address indexed user, uint256 indexed fuseTime);

    modifier adminOrOwner {
        address sender = _msgSender();
        require(sender == adminAddress || sender == owner(), "Address not admin or owner");
        _;
    }

    modifier onlyAdmin {
        require(_msgSender() == adminAddress, "Address not admin");
        _;
    }

    /// @param name is the name of the contract and piece
    /// @param symbol is the symbol
    /// @param royaltyRecipient is the royalty recipient
    /// @param royaltyPercentage is the royalty percentage to set
    /// @param admin is the admin address
    /// @param min is the minimum number of editions
    /// @param max is the maximum number of editions
    /// @param time is time after which replication can occur
    constructor (
        string memory name,
        string memory symbol,
        address royaltyRecipient,
        uint256 royaltyPercentage,
        address admin,
        uint256 min,
        uint256 max,
        uint256 time
    )
        ERC721S(name, symbol)
        EIP2981AllToken(royaltyRecipient, royaltyPercentage)
        Ownable() 
    {  
        adminAddress = admin;
        if (min < 1) {
            minShatters = 1;
        } else {
            minShatters = min;
        }
        maxShatters = max;
        shatterTime = time;
    }

    /// @notice function to change the royalty info
    /// @dev requires owner
    /// @dev this is useful if the amount was set improperly at contract creation.
    /// @param newAddr is the new royalty payout addresss
    /// @param newPerc is the new royalty percentage, in basis points (out of 10,000)
    function setRoyaltyInfo(address newAddr, uint256 newPerc) external onlyOwner {
        _setRoyaltyInfo(newAddr, newPerc);
    }

    /// @notice function to renounce admin rights
    /// @dev requires only admin
    function renounceAdmin() external onlyAdmin {
        adminAddress = address(0);
    }

    /// @notice function to set the admin address on the contract
    /// @dev requires owner
    /// @param newAdmin is the new admin address
    function setAdminAddress(address newAdmin) external onlyOwner {
        require(newAdmin != address(0), "New admin cannot be the zero address");
        adminAddress = newAdmin;
    }

    /// @notice function to set base uri
    /// @dev requires owner
    /// @param newUri is the new base uri
    function setBaseURI(string memory newUri) public onlyOwner {
        _setBaseUri(newUri);
    }

    /// @notice function for minting the 1/1 to the owner's address
    /// @dev requires contract owner or admin
    /// @dev sets the description, image, animation url (if exists), and traits for the piece
    /// @dev requires that shatters is equal to 0 -> meaning no piece has been minted
    /// @dev using _mint function as owner() should always be an EOA or trusted entity that can receive ERC721 tokens
    function mint(string memory newUri) external adminOrOwner {
        require(shatters == 0, "Already minted the first piece");
        _setBaseUri(newUri);
        shatters = 1;
        _mint(owner(), 0);
    }

    /// @notice function for owner of token 0 to unlock the piece and turn it into an edition
    /// @dev requires msg.sender to be the owner of token 0
    /// @dev requires a number of editions less than or equal to maxShatters or greater than or equal to minShatters
    /// @dev requires isShattered to be false
    /// @dev requires block timestamp to be greater than or equal to shatterTime
    /// @dev purposefully not letting approved addresses shatter as we want owner to be the only one to shatter the token
    /// @dev if number of editions == 1, fuse occurs at the same time
    /// @param numShatters is the total number of editions to make. Can be set between minShatters and maxShatters. This number is the total number of editions that will live on this contract
    function shatter(uint256 numShatters) external {
        address sender = _msgSender();
        require(!isShattered, "Already is shattered");
        require(sender == ownerOf(0), "Caller is not owner of token 0");
        require(numShatters >= minShatters && numShatters <= maxShatters, "Cannot set number of editions above max or below the min");
        require(block.timestamp >= shatterTime, "Cannot shatter prior to shatterTime");

        if (numShatters > 1) {
            _burn(0);
            _batchMint(sender, numShatters);
            emit Shattered(sender, numShatters, block.timestamp);
        } else {
            isFused = true;
            emit Shattered(sender, numShatters, block.timestamp);
            emit Fused(sender, block.timestamp);
        }
        // no reentrancy so can set these after burning and minting
        isShattered = true;
        shatters = numShatters;
    }

    /// @notice function to fuse editions back into a 1/1
    /// @dev requires msg.sender to own all of the editions
    /// @dev can't have already fused
    /// @dev must be shattered
    /// @dev purposefully not letting approved addresses fuse as we want the owner to have only control over fusing
    function fuse() external {
        require(!isFused, "Already is fused");
        require(isShattered, "Can't fuse if not already shattered");
        address sender = _msgSender();
        for (uint256 id = 1; id < shatters + 1; id++) {
            require(sender == ownerOf(id), "Msg sender must own all editions");
            _burn(id);
        }
        isFused = true;
        shatters = 1;
        _mint(sender, 0);

        emit Fused(sender, block.timestamp);
    }

    /// @notice overrides supportsInterface function
    /// @param interfaceId is supplied from anyone/contract calling this function, as defined in ERC 165
    /// @return boolean saying if this contract supports the interface or not
    function supportsInterface(bytes4 interfaceId) public view override(ERC721S, EIP2981AllToken) returns (bool) {
        return ERC721S.supportsInterface(interfaceId) || EIP2981AllToken.supportsInterface(interfaceId);
    }

    /// @notice function to override ownerOf in ERC721S
    /// @dev if is shattered and not fused, checks to see if that token has been transferred or if it belongs to the _shatterAddress.
    ///     Otherwise, returns result from ERC721S.
    function ownerOf(uint256 tokenId) public view virtual override(ERC721S) returns (address) {
        if (isShattered && !isFused) {
            if (tokenId > 0 && tokenId <= shatters) {
                address owner = _owners[tokenId];
                if (owner == address(0)) {
                    return _shatterAddress;
                } else {
                    return owner;
                }
            } else {
                revert("Invalid token id");
            }
        } else {
            return ERC721S.ownerOf(tokenId);
        }
    }

    /// @notice function to override the _exists function in ERC721S
    /// @dev if is shattered and not fused, checks to see if tokenId is in the range of shatters
    ///     otherwise, returns result from ERC721S
    function _exists(uint256 tokenId) internal view virtual override(ERC721S) returns (bool) {
        if (isShattered && !isFused) {
            if (tokenId > 0 && tokenId <= shatters) {
                return true;
            } else {
                return false;
            }
        } else {
            return ERC721S._exists(tokenId);
        }
    }

    /// @notice function to batch mint upon shatter
    /// @dev only mints tokenIds 1 -> quantity to shatterExecutor
    function _batchMint(address shatterExecutor, uint256 quantity) internal {
        _shatterAddress = shatterExecutor;
        _balances[shatterExecutor] += quantity;
        for (uint256 id = 1; id < quantity + 1; id++) {
            emit Transfer(address(0), shatterExecutor, id);
        }
    }

    /// @notice function to set base uri internally
    function _setBaseUri(string memory newUri) internal {
        _baseUri = newUri;
    }

    /// @notice override _baseURI() function from ERC721A
    function _baseURI() internal view override returns (string memory) {
        return _baseUri;
    }
}