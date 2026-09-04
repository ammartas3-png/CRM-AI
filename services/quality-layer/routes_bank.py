"""Example banks for ambiguous CRM comment families."""

from __future__ import annotations

ROUTE_BANK: dict[str, dict] = {
    "soft_money_call_again": {
        "status": "Call Again",
        "family": "money",
        "examples": [
            "no money until salary then will start",
            "dont have money will get my salary in few days then i can proceed",
            "cannot afford now will get help from someone and deposit",
            "dont have the funds give me some time to source for the funds",
            "have no funds will try to arrange the funds callback next week",
            "cant afford now callback next week she will get the funds",
            "dont have the amount will bring then continue",
            "17k ask friends borrow call again once more",
        ],
    },
    "hard_money_no_potential": {
        "status": "No Potential",
        "family": "money",
        "examples": [
            "student no money no job not sure when he can get money",
            "no money funding her business no money to invest now",
            "cannot afford after declined deposit dropped the call",
            "cant afford the minimum investment capital",
            "almost no money no savings barely makes ends meet",
            "dont have money cancel it was a mistake",
            "not serious didnt mean to invest no money",
        ],
    },
    "agent_redial_not_callback": {
        "status": "No Answer 1-5",
        "family": "callback",
        "examples": [
            "cb na vm",
            "cb : vm",
            "called back puhu",
            "i said i would hang up and call back but they didnt answer",
            "when i tried to cb she rejected na vm",
            "pu intro hu cb rej",
            "call again rej",
            "cb and she rej playing games",
        ],
    },
    "real_customer_callback": {
        "status": "Call Again",
        "family": "callback",
        "examples": [
            "pu said to call him later",
            "pu later im busy hu",
            "said he is busy call back later",
            "call me back tomorrow at 2",
            "needs time for amount reply to email",
            "says cb in an hour",
        ],
    },
    "single_refusal_recall": {
        "status": "Recall",
        "family": "refusal",
        "examples": [
            "playing around kept laughing didnt give me time",
            "not interest and she directly hu",
            "leave it hard refuse wont do anything",
            "dont want hung up",
            "registered by mistake doesnt want to invest",
            "lets stop i cant understand",
        ],
    },
    "language_barrier": {
        "status": "No Language",
        "family": "language",
        "examples": [
            "pu no english hu",
            "mandarin speaker tried english limited",
            "he only speaks the language of his country",
            "pu said no english huasa hu",
        ],
    },
}


def all_examples() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for name, meta in ROUTE_BANK.items():
        for ex in meta["examples"]:
            out.append((name, meta["status"], ex))
    return out
