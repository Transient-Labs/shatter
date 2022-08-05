// SPDX-License-Identifier: Apache-2.0

/// @title Shatter Creator
/// @author transientlabs.xyz

pragma solidity ^0.8.9;

import "OpenZeppelin/openzeppelin-contracts@4.6.0/contracts/proxy/ERC1967/ERC1967Proxy.sol";

contract ShatterCreatorV1Test is ERC1967Proxy {

    /// @param _impAddr is the logic contract implementation address
    /// @param _name is the name of the contract and piece
    /// @param _symbol is the symbol
    /// @param _royaltyRecipient is the royalty recipient
    /// @param _royaltyPercentage is the royalty percentage to set
    /// @param _admin is the admin address
    /// @param _minShatters is the minimum number of editions
    /// @param _maxShatters is the maximum number of editions
    /// @param _shatterTime is time after which replication can occur
    constructor(address _impAddr, string memory _name, string memory _symbol,
        address _royaltyRecipient, uint256 _royaltyPercentage, address _admin,
        uint256 _minShatters, uint256 _maxShatters, uint256 _shatterTime)
        ERC1967Proxy(_impAddr, abi.encodeWithSignature(
            "initialize(string,string,address,uint256,address,uint256,uint256,uint256)",
            _name, _symbol, _royaltyRecipient, _royaltyPercentage, _admin,  _minShatters, _maxShatters, _shatterTime))
        {
        }
}