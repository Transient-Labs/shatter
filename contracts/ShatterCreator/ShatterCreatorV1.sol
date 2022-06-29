// SPDX-License-Identifier: GPL-3.0-or-later

/// @title Shatter Creator
/// @author Transient Labs

pragma solidity ^0.8.9;

import "OpenZeppelin/openzeppelin-contracts@4.6.0/contracts/proxy/ERC1967/ERC1967Proxy.sol";

interface IShatterRegistry {
    function verifyContract(address _user, bytes memory _sig) external;
}

contract ShatterCreatorV1 is ERC1967Proxy {

    /// @param _name is the name of the contract and piece
    /// @param _symbol is the symbol
    /// @param _royaltyRecipient is the royalty recipient
    /// @param _royaltyPercentage is the royalty percentage to set
    /// @param _admin is the admin address
    /// @param _minShatters is the minimum number of replicates
    /// @param _maxShatters is the maximum number of replicates
    /// @param _shatterTime is time after which replication can occur
    /// @param _sig is an EIP 191 signature signed by the trusted Transient Labs portal to verify that this is an official Shatter contract
    constructor(string memory _name, string memory _symbol,
        address _royaltyRecipient, uint256 _royaltyPercentage, address _admin,
        uint256 _minShatters, uint256 _maxShatters, uint256 _shatterTime, bytes memory _sig)
        ERC1967Proxy(address(0), abi.encodeWithSignature(
            "initialize(string,string,address,uint256,address,uint256,uint256,uint256)",
            _name, _symbol, _royaltyRecipient, _royaltyPercentage, _admin, _minShatters, _maxShatters, _shatterTime))
        {
            // IShatterRegistry(0x...).verifyContract(msg.sender, _sig);
        }
}