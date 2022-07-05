from brownie import ShatterCoreV1, ShatterCreatorV1Test, accounts, reverts, chain
from brownie.network.contract import Contract
import pytest
import base64
import json

shatter_time = int(chain.time() + 2 * 3600)
desc = "An amazing description"
img = "ipfs://IMAGE"
anim = "ipfs://ANIM"
trait_names = ["T1", "T2", "T3"]
trait_values = ["V1", "V2", "V3"]

def get_uri(contract, token_id):
    uri = contract.tokenURI(token_id)[29:].encode("utf-8")
    decoded_uri = base64.b64decode(uri).decode("utf-8")
    json_uri = json.loads(decoded_uri)
    return json_uri

def get_trait_dict(attributes):
    traits = dict()
    for attribute in attributes:
        traits[attribute["trait_type"]] = attribute["value"]
    return traits

@pytest.fixture(scope="class")
def logic_contract():
    return ShatterCoreV1.deploy({"from": accounts[9]})

@pytest.fixture(scope="class")
def contract(logic_contract):
    proxy_contract = ShatterCreatorV1Test.deploy(logic_contract.address, "Test", "TST", accounts[1].address, 500, 1, 100, shatter_time, {"from": accounts[0]})
    return Contract.from_abi("ShatterContract", proxy_contract.address, logic_contract.abi)

class TestDefault:

    def test_default_values(self, contract):
        recp, amt = contract.royaltyInfo(1, 10000)
        assert (
            contract.owner() == accounts[0].address and
            contract.name() == "Test" and
            contract.symbol() == "TST" and
            contract.minShatters() == 1 and
            contract.maxShatters() == 100 and
            contract.shatterTime() == shatter_time and
            recp == accounts[1].address and
            amt == 500
        )

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

    def test_mint_non_admin_owner(self, contract):
        with reverts("Ownable: caller is not the owner"):
            contract.mint(desc, img, anim, trait_names, trait_values, {"from": accounts[3]})

class TestOwnerAccess:
    
    def test_mint(self, contract):
        contract.mint(desc, img, anim, trait_names, trait_values, {"from": accounts[0]})
        assert contract.ownerOf(0) == accounts[0].address

class TestShatter:

    def test_shatter_non_owner(self, contract):
        contract.mint(desc, img, anim, trait_names, trait_values, {"from": accounts[0]})
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
        t = int(shatter_time - chain.time())
        chain.sleep(t)
        contract.shatter(100, {"from": accounts[0]})
        assert contract.balanceOf(accounts[0].address) == 100

    def test_shatter_again(self, contract):
        with reverts("Already is shattered"):
            contract.shatter(100, {"from": accounts[0]})

class TestShatterByFirstBuyer:

    def test_shatter(self, contract):
        contract.mint(desc, img, anim, trait_names, trait_values, {"from": accounts[0]})
        contract.safeTransferFrom(accounts[0].address, accounts[5].address, 0, {"from": accounts[0]})
        contract.shatter(10, {"from": accounts[5]})
        assert contract.balanceOf(accounts[5].address) == 10

class TestShatterMultipleTransfers:

    def test_replicate(self, contract):
        contract.mint(desc, img, anim, trait_names, trait_values, {"from": accounts[0]})
        contract.safeTransferFrom(accounts[0].address, accounts[5].address, 0, {"from": accounts[0]})
        contract.safeTransferFrom(accounts[5].address, accounts[6].address, 0, {"from": accounts[5]})
        contract.shatter(10, {"from": accounts[6]})
        assert contract.balanceOf(accounts[6].address) == 10

class TestFuse:
    def test_fuse_not_shattered(self, contract):
        contract.mint(desc, img, anim, trait_names, trait_values, {"from": accounts[0]})
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
        assert contract.balanceOf(accounts[0].address) == 1 and contract.ownerOf(101) == accounts[0].address

    def test_fuse_again(self, contract):
        with reverts("Already is fused"):
            contract.fuse({"from": accounts[0]})

class TestTokenURISingleImage:
    def test_token_uri_init(self, contract):
        contract.mint(desc, img, "", trait_names, trait_values, {"from": accounts[0]})
        uri = get_uri(contract, 0)
        traits = get_trait_dict(uri["attributes"])
        assert (
            uri["name"] == "Test" and
            uri["description"] == desc and
            uri["image"] == img and
            traits["Shattered"] == "No" and
            traits["Fused"] == "No" and
            traits["T1"] == "V1" and
            traits["T2"] == "V2" and
            traits["T3"] == "V3"
        )

    def test_shatter_to_one_of_one(self, contract):
        tx = contract.shatter(1, {"from": accounts[0]})
        uri = get_uri(contract, 0)
        traits = get_trait_dict(uri["attributes"])
        assert (
            contract.balanceOf(accounts[0].address) == 1 and
            contract.ownerOf(0) == accounts[0].address and
            uri["name"] == "Test" and
            uri["description"] == desc and
            uri["image"] == img and
            traits["Shattered"] == "Yes" and
            traits["Fused"] == "Yes" and
            traits["T1"] == "V1" and
            traits["T2"] == "V2" and
            traits["T3"] == "V3" and
            "Shattered" in tx.events.keys() and
            tx.events["Shattered"]["_user"] == accounts[0].address and
            tx.events["Shattered"]["_numShatters"] == 1 and
            "Fused" in tx.events.keys() and
            tx.events["Fused"]["_user"] == accounts[0].address
        ) 

class TestTokenURIMultipleImageOnly:
    def test_shatter_half_max(self, contract):
        contract.mint(desc, img, "", trait_names, trait_values, {"from": accounts[0]})
        tx = contract.shatter(50, {"from": accounts[0]})
        uri = get_uri(contract, 1)
        traits = get_trait_dict(uri["attributes"])
        assert (
            contract.balanceOf(accounts[0].address) == 50 and
            uri["name"] == "Test #1/50" and
            uri["description"] == desc and
            uri["image"] == img and
            traits["Edition"] == "1" and
            traits["Shattered"] == "Yes" and
            traits["Fused"] == "No" and
            traits["T1"] == "V1" and
            traits["T2"] == "V2" and
            traits["T3"] == "V3" and
            "Shattered" in tx.events.keys() and
            tx.events["Shattered"]["_user"] == accounts[0].address and
            tx.events["Shattered"]["_numShatters"] == 50 and
            "Fused" not in tx.events.keys()
        )
    
    def test_fuse(self, contract):
        tx = contract.fuse({"from": accounts[0]})
        uri = get_uri(contract, 51)
        traits = get_trait_dict(uri["attributes"])
        assert (
            contract.balanceOf(accounts[0].address) == 1 and
            uri["name"] == "Test" and
            uri["description"] == desc and
            uri["image"] == img and
            traits["Shattered"] == "Yes" and
            traits["Fused"] == "Yes" and
            traits["T1"] == "V1" and
            traits["T2"] == "V2" and
            traits["T3"] == "V3" and
            "Shattered" not in tx.events.keys() and
            "Fused" in tx.events.keys() and
            tx.events["Fused"]["_user"] == accounts[0].address
        )

class TestTokenURISingleAnimation:
    def test_token_uri_init(self, contract):
        contract.mint(desc, img, anim, trait_names, trait_values, {"from": accounts[0]})
        uri = get_uri(contract, 0)
        traits = get_trait_dict(uri["attributes"])
        assert (
            uri["name"] == "Test" and
            uri["description"] == desc and
            uri["image"] == img and
            uri["animation_url"] == anim and
            traits["Shattered"] == "No" and
            traits["Fused"] == "No" and
            traits["T1"] == "V1" and
            traits["T2"] == "V2" and
            traits["T3"] == "V3"
        )

    def test_shatter_to_one_of_one(self, contract):
        tx = contract.shatter(1, {"from": accounts[0]})
        uri = get_uri(contract, 0)
        traits = get_trait_dict(uri["attributes"])
        assert (
            contract.balanceOf(accounts[0].address) == 1 and
            contract.ownerOf(0) == accounts[0].address and
            uri["name"] == "Test" and
            uri["description"] == desc and
            uri["image"] == img and
            uri["animation_url"] == anim and
            traits["Shattered"] == "Yes" and
            traits["Fused"] == "Yes" and
            traits["T1"] == "V1" and
            traits["T2"] == "V2" and
            traits["T3"] == "V3" and
            "Shattered" in tx.events.keys() and
            tx.events["Shattered"]["_user"] == accounts[0].address and
            tx.events["Shattered"]["_numShatters"] == 1 and
            "Fused" in tx.events.keys() and
            tx.events["Fused"]["_user"] == accounts[0].address
        ) 

class TestTokenURIMultipleAnimation:
    def test_shatter_half_max(self, contract):
        contract.mint(desc, img, anim, trait_names, trait_values, {"from": accounts[0]})
        tx = contract.shatter(50, {"from": accounts[0]})
        uri = get_uri(contract, 1)
        traits = get_trait_dict(uri["attributes"])
        assert (
            contract.balanceOf(accounts[0].address) == 50 and
            uri["name"] == "Test #1/50" and
            uri["description"] == desc and
            uri["image"] == img and
            uri["animation_url"] == anim and
            traits["Edition"] == "1" and
            traits["Shattered"] == "Yes" and
            traits["Fused"] == "No" and
            traits["T1"] == "V1" and
            traits["T2"] == "V2" and
            traits["T3"] == "V3" and
            "Shattered" in tx.events.keys() and
            tx.events["Shattered"]["_user"] == accounts[0].address and
            tx.events["Shattered"]["_numShatters"] == 50 and
            "Fused" not in tx.events.keys()
        )
    
    def test_fuse(self, contract):
        tx = contract.fuse({"from": accounts[0]})
        uri = get_uri(contract, 51)
        traits = get_trait_dict(uri["attributes"])
        assert (
            contract.balanceOf(accounts[0].address) == 1 and
            uri["name"] == "Test" and
            uri["description"] == desc and
            uri["image"] == img and
            uri["animation_url"] == anim and
            traits["Shattered"] == "Yes" and
            traits["Fused"] == "Yes" and
            traits["T1"] == "V1" and
            traits["T2"] == "V2" and
            traits["T3"] == "V3" and
            "Shattered" not in tx.events.keys() and
            "Fused" in tx.events.keys() and
            tx.events["Fused"]["_user"] == accounts[0].address
        )