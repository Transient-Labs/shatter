// SPDX-License-Identifier: GPL-3.0-or-later

/// @title Shatter Registry
/// @author transientlabs.xyz

pragma solidity ^0.8.9;

import "OpenZeppelin/openzeppelin-contracts@4.6.0/contracts/proxy/ERC1967/ERC1967Proxy.sol";

contract ShatterRegistry is ERC1967Proxy {
    constructor() ERC1967Proxy(0x31e91DA8Ec00A9E6d245b308386D18ba9B347f12, abi.encodeWithSignature("initialize()")) {}
}