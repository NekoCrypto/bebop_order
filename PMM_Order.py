import json
import time
import requests
from typing import Union, Literal

from eth_account import Account

from eth_account.datastructures import SignedMessage
from eth_account.messages import SignableMessage, encode_structured_data



# ============================ Models Data ============================ #
NAME = 'Bebop V2 Order'
AVAILABLE_NETWORKS = {'arbitrum': 42161, 'polygon': 137}

EXAMPLE_SWAP_ARBITRUM = {
    'USDT_ARBITRUM': '0x55d398326f99059fF775485246999027B3197955',
    'USDC_ARBITRUM': '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
    'DAI_ARBITRUM': '0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3',
    }

WALLET_ADDRESS = ''
PRIVATE_KEY = ''
AMOUNT = 1000000000 # Must Be in WEI
'''
proxy = {
    'http': user:pass@ip:port,
    'https': user:pass@ip:port,
}
'''

# ============================ 30 Days For Allowance ============================ #
expiration = int(time.time() + 2592025)

# ============================ QUOTE ============================ #
headers = {
    'accept': 'application/jsoncurl, */*',
    'authority': 'api.bebop.xyz',
    'accept-language': 'en-CA,en-GB;q=0.9,en;q=0.8',
    'origin': 'https://bebop.xyz',
    'referer': 'https://bebop.xyz/',
    'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
}
# One Token Swap Params
params_swap = {
    "buy_tokens": [f'{EXAMPLE_SWAP_ARBITRUM["USDT_ARBITRUM"]}'],
    "sell_tokens": [f'{EXAMPLE_SWAP_ARBITRUM['USDC_ARBITRUM']}'],
    "sell_amounts": str(f'{AMOUNT}'),
    "taker_address": f'{WALLET_ADDRESS}',
    "receiver_address": f'{WALLET_ADDRESS}',
    "source": "bebop",
    "approval_type": "Standard",
}
# Two Tokens Swap(Multi Swap) Params
params_multi_swap = {
    "buy_tokens": [
        f'{EXAMPLE_SWAP_ARBITRUM["USDT_ARBITRUM"]},{EXAMPLE_SWAP_ARBITRUM["DAI_ARBITRUM"]}'],
    "sell_tokens": [f'{EXAMPLE_SWAP_ARBITRUM['USDC_ARBITRUM']}'],
    "sell_amounts": str(f'{AMOUNT}'),
    "taker_address": f'{WALLET_ADDRESS}',
    "receiver_address": f'{WALLET_ADDRESS}',
    "source": "bebop",
    "approval_type": "Standard",
    'buy_tokens_ratios': '0.5,0.5',
}
response = requests.get(
    'https://api.bebop.xyz/router/arbitrum/v1/quote',
    params=params_swap,  # Or params_multi_swap
    headers=headers,
    # proxies=proxy
)
quote = {}
if response.status_code == 200:
    try:
        quote = response.json()
    except json.decoder.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
else:
    print(f"Request failed with status code: {response.status_code}")

i = 0
if "PMM" in quote["routes"][0]["type"]:
    i = 1

# ============================ Get Nonce ============================ #
contract = '0x000000000022d473030f116ddee9f6b43ac78ba3'  # Init Contract and add ABI nonce.json
nonce = contract.functions.allowance(
    WALLET_ADDRESS,
    EXAMPLE_SWAP_ARBITRUM['USDC_ARBITRUM'],
    '0xbeb09000fa59627dc02bb55448ac1893eaa501a5'
).call()

# ============================ Permit ============================ #
permit_message = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"}
        ],
        "PermitBatch": [
            {"name": "details", "type": "PermitDetails[]"},
            {"name": "spender", "type": "address"},
            {"name": "sigDeadline", "type": "uint256"}
        ],
        "PermitDetails": [
            {"name": "token", "type": "address"},
            {"name": "amount", "type": "uint160"},
            {"name": "expiration", "type": "uint48"},
            {"name": "nonce", "type": "uint48"}
        ]
    },
    "primaryType": "PermitBatch",
    "domain": {
        "name": "Permit2",
        "chainId": AVAILABLE_NETWORKS['arbitrum'],
        "verifyingContract": '0x000000000022d473030f116ddee9f6b43ac78ba3'
    },
    "message": {
        "details": [
            {
                "token": f'{EXAMPLE_SWAP_ARBITRUM["USDC_ARBITRUM"]}',
                "amount": 1461501637330902918203684832716283019655932542975,
                "expiration": expiration,
                "nonce": int(nonce[2])
            }
        ],
        "spender": '0xfe96910cf84318d1b8a5e2a6962774711467c0be',
        "sigDeadline": expiration
    }
}

signature: SignableMessage = encode_structured_data(
    primitive=permit_message,
)
permit_signature: Union[SignedMessage, Literal[False]] = Account.sign_message(signature,PRIVATE_KEY)

# ============================ Signature ============================ #
message = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"}
        ],
        "JamOrder": [
            {"name": "taker", "type": "address"},
            {"name": "receiver", "type": "address"},
            {"name": "expiry", "type": "uint256"},
            {"name": "nonce", "type": "uint256"},
            {"name": "executor", "type": "address"},
            {"name": "minFillPercent", "type": "uint16"},
            {"name": "hooksHash", "type": "bytes32"},
            {"name": "sellTokens", "type": "address[]"},
            {"name": "buyTokens", "type": "address[]"},
            {"name": "sellAmounts", "type": "uint256[]"},
            {"name": "buyAmounts", "type": "uint256[]"},
            {"name": "sellNFTIds", "type": "uint256[]"},
            {"name": "buyNFTIds", "type": "uint256[]"},
            {"name": "sellTokenTransfers", "type": "bytes"},
            {"name": "buyTokenTransfers", "type": "bytes"}
        ]
    },
    "primaryType": "JamOrder",
    "domain": {
        "name": "JamSettlement",
        "version": "1",
        "chainId": AVAILABLE_NETWORKS["arbitrum"],
        "verifyingContract": '0xbeb09000fa59627dc02bb55448ac1893eaa501a5',
    },
    "message": {
        "expiry": int(quote["routes"][i]["quote"]["toSign"]["expiry"]),
        "taker": f"{WALLET_ADDRESS}",
        "receiver": f"{WALLET_ADDRESS}",
        "executor": quote["routes"][i]["quote"]["toSign"]["executor"],
        "minFillPercent": int(quote["routes"][i]["quote"]["toSign"]["minFillPercent"]),
        "nonce": int(quote["routes"][i]["quote"]["toSign"]["nonce"]),
        "hooksHash": bytes.fromhex(quote["routes"][i]["quote"]["toSign"]["hooksHash"][2:]),
        "sellTokens": quote["routes"][i]["quote"]["toSign"]["sellTokens"],
        "buyTokens": quote["routes"][i]["quote"]["toSign"]["buyTokens"],
        "sellAmounts": list(int(amount) for amount in quote["routes"][i]["quote"]["toSign"]["sellAmounts"]),
        "buyAmounts": list(int(amount) for amount in quote["routes"][i]["quote"]["toSign"]["buyAmounts"]),
        "sellNFTIds": [],
        "buyNFTIds": [],
        "sellTokenTransfers": bytes.fromhex(
            quote["routes"][i]["quote"]["toSign"]["sellTokenTransfers"][2:]),
        "buyTokenTransfers": bytes.fromhex(quote["routes"][i]["quote"]["toSign"]["buyTokenTransfers"][2:])
    }
}

signature: SignableMessage = encode_structured_data(
    primitive=message,
)
signature: Union[SignedMessage, Literal[False]] = Account.sign_message(signature, PRIVATE_KEY)

# ============================ Send Order ============================ #
# ============================ Approve Token ============================ #
'''
approve_interface(
        token_address=EXAMPLE_SWAP_ARBITRUM["USDC_ARBITRUM"],
        spender="0xbeb09000fa59627dc02bb55448ac1893eaa501a5",
        amount=AMOUNT
)
'''

# ============================ V1 Jam Order Post ============================ #
order_data = {
    "quote_id": quote["routes"][i]["quote"]["quoteId"],
    "signature": signature.signature.hex(),
    "sign_scheme": "EIP712",
    'permit2': {
        'signature': permit_signature.signature.hex(),
        'approvals_deadline': expiration,
        'token_addresses': [f'{EXAMPLE_SWAP_ARBITRUM["USDC_ARBITRUM"]}'],
        'token_nonces': [int(nonce[2])],
    },
}
headers = {
    'authority': 'api.bebop.xyz',
    'accept': '*/*',
    'accept-language': 'en-CA,en-GB;q=0.9,en;q=0.8',
    'cache-control': 'max-age=0',
    'content-type': 'application/json; charset=utf-8',
    'origin': 'https://bebop.xyz',
    'referer': 'https://bebop.xyz/',
    'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
}

response = requests.post(
    f"https://api.bebop.xyz/arbitrum/v2/order",
    data=json.dumps(order_data),
    headers=headers,
    # proxies=proxy
)
status = response.json()
print(json.dumps(status, indent=4))

# ============================ Order Status Checker ============================ #
headers = {
    'authority': 'api.bebop.xyz',
    'accept': '*/*',
    'accept-language': 'en-CA,en-GB;q=0.9,en;q=0.8',
    'cache-control': 'max-age=0',
    'content-type': 'application/json; charset=utf-8',
    'origin': 'https://bebop.xyz',
    'referer': 'https://bebop.xyz/',
    'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
}

params = {
    'quote_id': quote["routes"][i]["quote"]["quoteId"],
}
response_status = {
    "status": "Pending",
}

while response_status['status'] != 'Settled':
    response_status = requests.get(
        f"https://api.bebop.xyz/arbitrum/v2/order-status",
        params=params,
        headers=headers,
        # proxies=proxy
    ).json()

if response_status['status'] == 'Settled':
    print(json.dumps(response_status, indent=4))
