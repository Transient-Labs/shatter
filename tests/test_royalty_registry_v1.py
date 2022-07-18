from brownie import ShatterRegistryTest, ShatterRegistryEngineV1, accounts, reverts
from brownie.network.contract import Contract
from evm_sc_utils.signers import EIP191Signer
import pytest
from secrets import token_hex

signer = EIP191Signer()

@pytest.fixture(scope="class")
def logic_contract():
    return ShatterRegistryEngineV1.deploy({"from": accounts[9]})

@pytest.fixture(scope="class")
def contract(logic_contract):
    proxy_contract = ShatterRegistryTest.deploy(logic_contract.address, {"from": accounts[0]})
    return Contract.from_abi("ShatterRegistry", proxy_contract.address, logic_contract.abi)

class TestInterfaces:

    def test_erc165_interface(self, contract):
        assert contract.supportsInterface("0x01ffc9a7")

class TestDefaultValues:

    def test_owner(self, contract):
        assert contract.owner() == accounts[0].address

class TestAccess:

    def test_initialize(self, contract):
        with reverts():
            contract.initialize({"from": accounts[1]})

    def test_register(self, contract):
        with reverts("Invalid signature supplied"):
            nonce = token_hex(32)
            sig = signer.sign(["address", "uint256", "bytes32"], [accounts[2].address, 1, nonce]).signature
            contract.register(accounts[1].address, 1, nonce, sig, {"from": accounts[1]})

    def test_manual_register(self, contract):
        with reverts("Ownable: caller is not the owner"):
            contract.manuallyRegister(accounts[1].address, accounts[2].address, 1, {"from": accounts[1]})

    def test_upgrade(self, contract):
        with reverts("Ownable: caller is not the owner"):
            contract.upgradeTo(accounts[3].address, {"from": accounts[1]})

    def test_signer(self, contract):
        with reverts("Ownable: caller is not the owner"):
            contract.setSigner(accounts[1].address, {"from": accounts[1]})

class TestRegistry:

    def test_set_signer(self, contract):
        contract.setSigner(signer.address, {"from": accounts[0]})
        assert contract.signer() == signer.address

    def test_manual_register(self, contract):
        contract.manuallyRegister(accounts[1].address, accounts[2].address, 1, {"from": accounts[0]})
        tf, version = contract.lookup(accounts[2].address)
        assert tf and version == 1

    def test_register(self, contract):
        nonce = token_hex(32)
        sig = signer.sign(["address", "uint256", "bytes32"], [accounts[2].address, 1, nonce]).signature
        contract.register(accounts[2].address, 1, nonce, sig, {"from": accounts[1]})
        tf, version = contract.lookup(accounts[1].address)
        assert tf and version == 1

    def test_register_already_registered(self, contract):
        nonce = token_hex(32)
        sig = signer.sign(["address", "uint256", "bytes32"], [accounts[2].address, 1, nonce]).signature
        with reverts("Already registered"):
            contract.register(accounts[2].address, 1, nonce, sig, {"from": accounts[1]})

    def test_register_same_nonce(self, contract):
        nonce = token_hex(32)
        sig = signer.sign(["address", "uint256", "bytes32"], [accounts[3].address, 1, nonce]).signature
        contract.register(accounts[3].address, 1, nonce, sig, {"from": accounts[4]})
        with reverts("Nonce already has been used"):
            contract.register(accounts[3].address, 1, nonce, sig, {"from": accounts[3]})

    
