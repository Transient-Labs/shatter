from brownie import Shatter, accounts, reverts, chain
from datetime import datetime as dt
from datetime import timedelta as td
import pytest
import base64

single_token_uri = "data:application/json;base64," + base64.b64encode('{"name": "Test","description": "Super awesome description","attributes": [{"trait_type": "T1", "value": "V1"},{"trait_type": "T2", "value": "V2"},{"trait_type": "Shattered", "value": "No"},{"trait_type": "Fused", "value": "No"}],"image": "testImage"}'.encode("utf-8")).decode("utf-8")
replicated_single_token = "data:application/json;base64," + base64.b64encode('{"name": "Test","description": "Super awesome description","attributes": [{"trait_type": "T1", "value": "V1"},{"trait_type": "T2", "value": "V2"},{"trait_type": "Shattered", "value": "Yes"},{"trait_type": "Fused", "value": "Yes"}],"image": "testImage"}'.encode("utf-8")).decode("utf-8")
multi_token_one = "data:application/json;base64," + base64.b64encode('{"name": "Test #1/10","description": "Super awesome description","attributes": [{"trait_type": "T1", "value": "V1"},{"trait_type": "T2", "value": "V2"},{"trait_type": "Edition", "value": "1"},{"trait_type": "Shattered", "value": "Yes"},{"trait_type": "Fused", "value": "No"}],"image": "testImage"}'.encode("utf-8")).decode("utf-8")
multi_token_two = "data:application/json;base64," + base64.b64encode('{"name": "Test #2/10","description": "Super awesome description","attributes": [{"trait_type": "T1", "value": "V1"},{"trait_type": "T2", "value": "V2"},{"trait_type": "Edition", "value": "2"},{"trait_type": "Shattered", "value": "Yes"},{"trait_type": "Fused", "value": "No"}],"image": "testImage"}'.encode("utf-8")).decode("utf-8")
fuse_token = "data:application/json;base64," + base64.b64encode('{"name": "Test","description": "Super awesome description","attributes": [{"trait_type": "T1", "value": "V1"},{"trait_type": "T2", "value": "V2"},{"trait_type": "Shattered", "value": "Yes"},{"trait_type": "Fused", "value": "Yes"}],"image": "testImage"}'.encode("utf-8")).decode("utf-8")

replicate_time = dt.now() + td(hours=2)

@pytest.fixture(scope="class")
def contract():
    return Shatter.deploy("Test", "TST", accounts[1].address, 500, accounts[2].address, 1, 100, int(dt.timestamp(replicate_time)), "Super awesome description", "testImage", {"from": accounts[0]})

class TestInterface:

    def test_erc721_interface(self, contract):
        assert contract.supportsInterface("0x80ac58cd")

    def test_eip2981_interface(self, contract):
        assert contract.supportsInterface("0x2a55205a")

    def test_erc165_interface(self, contract):
        assert contract.supportsInterface("0x01ffc9a7")

    def test_erc721_metadata_interface(self, contract):
        assert contract.supportsInterface("0x5b5e139f")

    
class TestNoAccess:

    def test_set_royalty_info_non_admin_owner(self, contract):
        with reverts("Address not admin or owner"):
            contract.setRoyaltyInfo(accounts[3].address, 750, {"from": accounts[3]})

    def test_set_admin_address_non_owner(self, contract):
        with reverts("Ownable: caller is not the owner"):
            contract.setAdminAddress(accounts[1].address, {"from": accounts[2]})
            contract.setAdminAddress(accounts[1].address, {"from": accounts[3]})

    def test_set_description_non_admin_owner(self, contract):
        with reverts("Address not admin or owner"):
            contract.setDescription("Super interesting description", {"from": accounts[3]})

    def test_set_traits_non_admin_owner(self, contract):
        with reverts("Address not admin or owner"):
            contract.setTraits(["T1"], ["V1"], {"from": accounts[3]})

    def test_mint_non_admin_owner(self, contract):
        with reverts("Address not admin or owner"):
            contract.mint({"from": accounts[3]})

class TestAdminAccess:

    def test_set_royalty_info(self, contract):
        contract.setRoyaltyInfo(accounts[3].address, 750, {"from": accounts[2]})
        (recp, amt) = contract.royaltyInfo(1, 1000)
        assert recp == accounts[3].address and amt == 1000*0.075
    
    def test_mint(self, contract):
        contract.mint({"from": accounts[2]})
        assert contract.ownerOf(0) == accounts[0].address

    def test_set_description(self, contract):
        contract.setDescription("Super awesome description", {"from": accounts[2]})

    def test_set_traits(self, contract):
        contract.setTraits(["T1"], ["V1"], {"from": accounts[2]})

    def test_shatter(self, contract):
        with reverts("Caller is not owner of token 0"):
            contract.shatter(10, {"from": accounts[2]})

    def test_fuse(self, contract):
        with reverts("Can't fuse if not already shattered"):
            contract.fuse({"from": accounts[2]})

class TestOwnerAccess:

    def test_set_royalty_info(self, contract):
        contract.setRoyaltyInfo(accounts[3].address, 750, {"from": accounts[0]})
        (recp, amt) = contract.royaltyInfo(1, 1000)
        assert recp == accounts[3].address and amt == 1000*0.075

    def test_set_description(self, contract):
        contract.setDescription("Super awesome description", {"from": accounts[0]})

    def test_set_traits(self, contract):
        contract.setTraits(["T1"], ["V1"], {"from": accounts[0]})
    
    def test_mint(self, contract):
        contract.mint({"from": accounts[0]})
        assert contract.ownerOf(0) == accounts[0].address

class TestShatter:

    def test_shatter_non_owner(self, contract):
        contract.mint({"from": accounts[2]})
        with reverts("Caller is not owner of token 0"):
            contract.shatter(10, {"from": accounts[1]})

    def test_shatter_less_than_min(self, contract):
        with reverts("Cannot set number of editions above max or below the min"):
            contract.shatter(0, {"from": accounts[0]})

    def test_shatter_more_than_max(self, contract):
        with reverts("Cannot set number of editions above max or below the min"):
            contract.shatter(101, {"from": accounts[0]})

    def test_shatter_before_shatter_time(self, contract):
        with reverts("Cannot shatter prior to shatterTime"):
            contract.shatter(10, {"from": accounts[0]})

    def test_create_max_shatter(self, contract):
        t = int(dt.timestamp(replicate_time) - chain.time())
        chain.sleep(t)
        contract.shatter(100, {"from": accounts[0]})
        assert contract.balanceOf(accounts[0].address) == 100

    def test_shatter_again(self, contract):
        with reverts("Already is shattered"):
            contract.shatter(100, {"from": accounts[0]})

class TestShatterSingle:
    def test_shatter_single(self, contract):
        contract.mint({"from": accounts[2]})
        contract.shatter(1, {"from": accounts[0]})
        assert contract.balanceOf(accounts[0].address) == 1

class TestShatterInBetween:
    def test_shatter_in_between(self, contract):
        contract.mint({"from": accounts[2]})
        contract.shatter(50, {"from": accounts[0]})
        assert contract.balanceOf(accounts[0].address) == 50

class TestShatterByFirstBuyer:

    def test_shatter(self, contract):
        contract.mint({"from": accounts[2]})
        contract.safeTransferFrom(accounts[0].address, accounts[5].address, 0, {"from": accounts[0]})
        contract.shatter(10, {"from": accounts[5]})
        assert contract.balanceOf(accounts[5].address) == 10

class TestShatterMultipleTransfers:

    def test_replicate(self, contract):
        contract.mint({"from": accounts[2]})
        contract.safeTransferFrom(accounts[0].address, accounts[5].address, 0, {"from": accounts[0]})
        contract.safeTransferFrom(accounts[5].address, accounts[6].address, 0, {"from": accounts[5]})
        contract.shatter(10, {"from": accounts[6]})
        assert contract.balanceOf(accounts[6].address) == 10

class TestTokenURIInitial:

    def test_initial(self, contract):
        contract.setTraits(["T1", "T2"], ["V1", "V2"], {"from": accounts[2]})
        contract.mint({"from": accounts[2]})
        token_uri = contract.tokenURI(0)
        assert token_uri == single_token_uri

class TestMultiTokenURI:

    def test_multi(self, contract):
        contract.setTraits(["T1", "T2"], ["V1", "V2"], {"from": accounts[2]})
        contract.mint({"from": accounts[2]})
        contract.shatter(10, {"from": accounts[0]})
        assert contract.tokenURI(1) == multi_token_one and contract.tokenURI(2) == multi_token_two

class TestSingleTokenURIForever:

    def test_single_forever(self, contract):
        contract.setTraits(["T1", "T2"], ["V1", "V2"], {"from": accounts[2]})
        contract.mint({"from": accounts[2]})
        contract.shatter(1, {"from": accounts[0]})
        assert contract.tokenURI(0) == replicated_single_token

class TestFuse:
    def test_fuse_not_shattered(self, contract):
        contract.setTraits(["T1", "T2"], ["V1", "V2"], {"from": accounts[2]})
        contract.mint({"from": accounts[2]})
        with reverts("Can't fuse if not already shattered"):
            contract.fuse({"from": accounts[0]})

    def test_fuse_not_owner_of_all(self, contract):
        contract.shatter(100, {'from': accounts[0]})
        contract.safeTransferFrom(accounts[0].address, accounts[1].address, 1, {"from": accounts[0]})
        with reverts():
            contract.fuse({"from": accounts[0]})

    def test_fuse_not_own_any(self, contract):
        with reverts():
            contract.fuse({"from": accounts[6]})

    def test_fuse_own_one(self, contract):
        with reverts():
            contract.fuse({"from": accounts[1]})

    def test_fuse(self, contract):
        contract.safeTransferFrom(accounts[1].address, accounts[0].address, 1, {"from": accounts[1]})
        contract.fuse({"from": accounts[0]})
        assert contract.balanceOf(accounts[0].address) == 1 and contract.tokenURI(101) == fuse_token

    def test_fuse_again(self, contract):
        with reverts("Already is fused"):
            contract.fuse({"from": accounts[0]})