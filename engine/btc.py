import hashlib

from engine.bech32 import BECH32, BECH32M, encode as bech32_encode
from engine.bip32 import XPRV, XPUB, ZPRV, ZPUB, Node, hash160
from engine.bip39 import mnemonic_to_seed, validate_mnemonic
from engine.charset import CharsetError
from engine.secp256k1 import N, tweak_add_pub

BTC_ACCOUNT = "m/84'/0'/0'"
BTC_FIRST = "m/84'/0'/0'/0/0"
TAP_ACCOUNT = "m/86'/0'/0'"


def p2wpkh_address(pub33, hrp="bc"):
    return bech32_encode(hrp, 0, hash160(pub33), BECH32)


def tagged_hash(tag, msg):
    digest = hashlib.sha256(tag).digest()
    return hashlib.sha256(digest + digest + msg).digest()


def p2tr_address(pub33, hrp="bc"):
    xonly = pub33[1:]
    tweak = int.from_bytes(tagged_hash(b"TapTweak", xonly), "big")
    if tweak >= N:
        raise CharsetError("invalid taproot tweak")
    even = b"\x02" + xonly
    tweaked = tweak_add_pub(even, tweak.to_bytes(32, "big"))
    return bech32_encode(hrp, 1, tweaked[1:], BECH32M)


def _chain(root, account_path, branch, count, make_addr):
    rows = []
    for i in range(count):
        path = "%s/%d/%d" % (account_path, branch, i)
        node = root.derive(path)
        rows.append({"index": i, "path": path, "address": make_addr(node.pub)})
    return rows


def derive_btc(mnemonic, passphrase="", receive=5, change=5, taproot=False):
    phrase = " ".join((mnemonic or "").split())
    if not validate_mnemonic(phrase):
        raise CharsetError("not a valid BIP-39 English mnemonic")
    receive = int(receive)
    change = int(change)
    if receive < 1 or receive > 20 or change < 0 or change > 20:
        raise CharsetError("address count out of range")
    seed = mnemonic_to_seed(phrase, passphrase or "")
    root = Node.from_seed(seed)
    account = root.derive(BTC_ACCOUNT)
    recv = _chain(root, BTC_ACCOUNT, 0, receive, p2wpkh_address)
    chg = _chain(root, BTC_ACCOUNT, 1, change, p2wpkh_address) if change else []
    out = {
        "path_account": BTC_ACCOUNT,
        "path_address": recv[0]["path"],
        "zpub": account.extended(False, ZPUB),
        "zprv": account.extended(True, ZPRV),
        "address": recv[0]["address"],
        "pubkey": root.derive(recv[0]["path"]).pub.hex(),
        "receive": recv,
        "change": chg,
        "taproot": None,
    }
    if taproot:
        t_account = root.derive(TAP_ACCOUNT)
        t_recv = _chain(root, TAP_ACCOUNT, 0, receive, p2tr_address)
        t_chg = _chain(root, TAP_ACCOUNT, 1, change, p2tr_address) if change else []
        out["taproot"] = {
            "path_account": TAP_ACCOUNT,
            "xpub": t_account.extended(False, XPUB),
            "xprv": t_account.extended(True, XPRV),
            "address": t_recv[0]["address"],
            "receive": t_recv,
            "change": t_chg,
        }
    return out
