"""
Aave V3 Contract Call Helper.

Generates calldata for Aave V3 Pool contract interactions.
Follows hexagonal architecture - this is infrastructure layer.

Contract ABI Function Signatures:
- supply(address asset, uint256 amount, address onBehalfOf, uint16 referralCode)
- borrow(address asset, uint256 amount, uint256 interestRateMode, uint16 referralCode, address onBehalfOf)
- repay(address asset, uint256 amount, uint256 interestRateMode, address onBehalfOf)
- withdraw(address asset, uint256 amount, address to)
- setUserUseReserveAsCollateral(address asset, bool useAsCollateral)
"""

import logging
from decimal import Decimal
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Aave V3 Pool function selectors (first 4 bytes of keccak256(signature))
AAVE_FUNCTION_SELECTORS = {
    "supply": "0x617ba037",  # supply(address,uint256,address,uint16)
    "borrow": "0xa415bcad",  # borrow(address,uint256,uint256,uint16,address)
    "repay": "0x573ade81",  # repay(address,uint256,uint256,address)
    "withdraw": "0x69328dec",  # withdraw(address,uint256,address)
    "setUserUseReserveAsCollateral": "0x5a3b74b9",  # setUserUseReserveAsCollateral(address,bool)
}

# Interest rate modes
INTEREST_RATE_STABLE = 1
INTEREST_RATE_VARIABLE = 2


def pad_address(address: str) -> str:
    """
    Pad Ethereum address to 32 bytes (64 hex chars).

    Args:
        address: Ethereum address (0x + 40 hex chars)

    Returns:
        Padded address (64 hex chars, no 0x prefix)
    """
    # Remove 0x prefix if present
    addr = address[2:] if address.startswith("0x") else address
    # Pad to 64 chars (32 bytes)
    return addr.lower().zfill(64)


def pad_uint256(value: int) -> str:
    """
    Pad uint256 value to 32 bytes (64 hex chars).

    Args:
        value: Integer value

    Returns:
        Padded hex string (64 chars, no 0x prefix)
    """
    # Convert to hex, remove 0x prefix, pad to 64 chars
    return hex(value)[2:].zfill(64)


def encode_supply_calldata(
    asset_address: str,
    amount_wei: int,
    on_behalf_of: str,
    referral_code: int = 0,
) -> str:
    """
    Encode calldata for Aave V3 Pool.supply() function.

    Function signature:
    supply(address asset, uint256 amount, address onBehalfOf, uint16 referralCode)

    Args:
        asset_address: Underlying asset address
        amount_wei: Amount to supply in wei (smallest unit)
        on_behalf_of: Address receiving the aTokens
        referral_code: Referral code (0 for none)

    Returns:
        Encoded calldata (0x + hex)
    """
    selector = AAVE_FUNCTION_SELECTORS["supply"]

    # Encode parameters
    asset = pad_address(asset_address)
    amount = pad_uint256(amount_wei)
    behalf = pad_address(on_behalf_of)
    referral = pad_uint256(referral_code)

    # Concatenate: selector + params
    calldata = f"{selector}{asset}{amount}{behalf}{referral}"

    logger.debug(f"Generated supply calldata for {asset_address}, amount: {amount_wei}")
    return calldata


def encode_borrow_calldata(
    asset_address: str,
    amount_wei: int,
    interest_rate_mode: int,  # 1 = stable, 2 = variable
    on_behalf_of: str,
    referral_code: int = 0,
) -> str:
    """
    Encode calldata for Aave V3 Pool.borrow() function.

    Function signature:
    borrow(address asset, uint256 amount, uint256 interestRateMode, uint16 referralCode, address onBehalfOf)

    Args:
        asset_address: Asset to borrow
        amount_wei: Amount to borrow in wei
        interest_rate_mode: 1 for stable, 2 for variable
        on_behalf_of: Address receiving the borrowed tokens
        referral_code: Referral code (0 for none)

    Returns:
        Encoded calldata (0x + hex)
    """
    selector = AAVE_FUNCTION_SELECTORS["borrow"]

    # Encode parameters
    asset = pad_address(asset_address)
    amount = pad_uint256(amount_wei)
    rate_mode = pad_uint256(interest_rate_mode)
    referral = pad_uint256(referral_code)
    behalf = pad_address(on_behalf_of)

    # Concatenate: selector + params
    calldata = f"{selector}{asset}{amount}{rate_mode}{referral}{behalf}"

    logger.debug(
        f"Generated borrow calldata for {asset_address}, amount: {amount_wei}, rate mode: {interest_rate_mode}"
    )
    return calldata


def encode_repay_calldata(
    asset_address: str,
    amount_wei: int,  # Use max uint256 for full repayment
    interest_rate_mode: int,
    on_behalf_of: str,
) -> str:
    """
    Encode calldata for Aave V3 Pool.repay() function.

    Function signature:
    repay(address asset, uint256 amount, uint256 interestRateMode, address onBehalfOf)

    Args:
        asset_address: Asset to repay
        amount_wei: Amount to repay in wei (use max uint256 for full repayment)
        interest_rate_mode: 1 for stable, 2 for variable
        on_behalf_of: Address whose debt is being repaid

    Returns:
        Encoded calldata (0x + hex)
    """
    selector = AAVE_FUNCTION_SELECTORS["repay"]

    # Encode parameters
    asset = pad_address(asset_address)
    amount = pad_uint256(amount_wei)
    rate_mode = pad_uint256(interest_rate_mode)
    behalf = pad_address(on_behalf_of)

    # Concatenate: selector + params
    calldata = f"{selector}{asset}{amount}{rate_mode}{behalf}"

    logger.debug(f"Generated repay calldata for {asset_address}, amount: {amount_wei}")
    return calldata


def encode_withdraw_calldata(
    asset_address: str,
    amount_wei: int,  # Use max uint256 for full withdrawal
    to_address: str,
) -> str:
    """
    Encode calldata for Aave V3 Pool.withdraw() function.

    Function signature:
    withdraw(address asset, uint256 amount, address to)

    Args:
        asset_address: Asset to withdraw
        amount_wei: Amount to withdraw in wei (use max uint256 for full withdrawal)
        to_address: Address receiving the withdrawn tokens

    Returns:
        Encoded calldata (0x + hex)
    """
    selector = AAVE_FUNCTION_SELECTORS["withdraw"]

    # Encode parameters
    asset = pad_address(asset_address)
    amount = pad_uint256(amount_wei)
    to = pad_address(to_address)

    # Concatenate: selector + params
    calldata = f"{selector}{asset}{amount}{to}"

    logger.debug(
        f"Generated withdraw calldata for {asset_address}, amount: {amount_wei}"
    )
    return calldata


def encode_set_collateral_calldata(
    asset_address: str,
    use_as_collateral: bool,
) -> str:
    """
    Encode calldata for Aave V3 Pool.setUserUseReserveAsCollateral() function.

    Function signature:
    setUserUseReserveAsCollateral(address asset, bool useAsCollateral)

    Args:
        asset_address: Asset address
        use_as_collateral: True to enable as collateral, False to disable

    Returns:
        Encoded calldata (0x + hex)
    """
    selector = AAVE_FUNCTION_SELECTORS["setUserUseReserveAsCollateral"]

    # Encode parameters
    asset = pad_address(asset_address)
    use_collateral = pad_uint256(1 if use_as_collateral else 0)

    # Concatenate: selector + params
    calldata = f"{selector}{asset}{use_collateral}"

    logger.debug(
        f"Generated setUserUseReserveAsCollateral calldata for {asset_address}: {use_as_collateral}"
    )
    return calldata


def wei_from_decimal(amount: str | Decimal, decimals: int) -> int:
    """
    Convert human-readable amount to wei (smallest unit).

    Args:
        amount: Human-readable amount (e.g., "100.5")
        decimals: Token decimals (e.g., 18 for ETH, 6 for USDC)

    Returns:
        Amount in wei (integer)
    """
    if isinstance(amount, str):
        amount = Decimal(amount)

    # Multiply by 10^decimals
    wei = int(amount * Decimal(10**decimals))
    return wei


def max_uint256() -> int:
    """
    Return max uint256 value (used for "full repayment" or "full withdrawal").

    Returns:
        2^256 - 1
    """
    return 2**256 - 1


def generate_supply_transaction(
    pool_address: str,
    asset_address: str,
    amount: str | Decimal,
    asset_decimals: int,
    user_address: str,
    use_as_collateral: bool = True,
) -> Dict[str, Any]:
    """
    Generate complete transaction data for Aave V3 supply operation.

    Args:
        pool_address: Aave V3 Pool contract address
        asset_address: Underlying asset to supply
        amount: Human-readable amount (e.g., "100.5")
        asset_decimals: Token decimals (6 for USDC, 18 for ETH)
        user_address: User's wallet address
        use_as_collateral: Whether to enable asset as collateral

    Returns:
        Transaction dictionary with to, data, value fields
    """
    amount_wei = wei_from_decimal(amount, asset_decimals)
    calldata = encode_supply_calldata(
        asset_address=asset_address,
        amount_wei=amount_wei,
        on_behalf_of=user_address,
        referral_code=0,
    )

    return {
        "to": pool_address,
        "data": calldata,
        "value": "0",  # No ETH sent (unless supplying native ETH via WETH gateway)
        "gas_limit": "400000",  # Estimated gas limit
    }


def generate_borrow_transaction(
    pool_address: str,
    asset_address: str,
    amount: str | Decimal,
    asset_decimals: int,
    user_address: str,
    rate_mode: str = "variable",  # "variable" or "stable"
) -> Dict[str, Any]:
    """
    Generate complete transaction data for Aave V3 borrow operation.

    Args:
        pool_address: Aave V3 Pool contract address
        asset_address: Asset to borrow
        amount: Human-readable amount
        asset_decimals: Token decimals
        user_address: User's wallet address
        rate_mode: "variable" or "stable"

    Returns:
        Transaction dictionary with to, data, value fields
    """
    amount_wei = wei_from_decimal(amount, asset_decimals)
    interest_rate_mode = (
        INTEREST_RATE_VARIABLE if rate_mode == "variable" else INTEREST_RATE_STABLE
    )

    calldata = encode_borrow_calldata(
        asset_address=asset_address,
        amount_wei=amount_wei,
        interest_rate_mode=interest_rate_mode,
        on_behalf_of=user_address,
        referral_code=0,
    )

    return {
        "to": pool_address,
        "data": calldata,
        "value": "0",
        "gas_limit": "500000",  # Estimated gas limit (borrow is more complex)
    }


def generate_repay_transaction(
    pool_address: str,
    asset_address: str,
    amount: str | Decimal,  # Use "max" for full repayment
    asset_decimals: int,
    user_address: str,
    rate_mode: str = "variable",
) -> Dict[str, Any]:
    """
    Generate complete transaction data for Aave V3 repay operation.

    Args:
        pool_address: Aave V3 Pool contract address
        asset_address: Asset to repay
        amount: Human-readable amount or "max" for full repayment
        asset_decimals: Token decimals
        user_address: User's wallet address
        rate_mode: "variable" or "stable"

    Returns:
        Transaction dictionary with to, data, value fields
    """
    if amount == "max" or (isinstance(amount, str) and amount.lower() == "max"):
        amount_wei = max_uint256()
    else:
        amount_wei = wei_from_decimal(amount, asset_decimals)

    interest_rate_mode = (
        INTEREST_RATE_VARIABLE if rate_mode == "variable" else INTEREST_RATE_STABLE
    )

    calldata = encode_repay_calldata(
        asset_address=asset_address,
        amount_wei=amount_wei,
        interest_rate_mode=interest_rate_mode,
        on_behalf_of=user_address,
    )

    return {
        "to": pool_address,
        "data": calldata,
        "value": "0",
        "gas_limit": "350000",  # Estimated gas limit
    }


def generate_withdraw_transaction(
    pool_address: str,
    asset_address: str,
    amount: str | Decimal,  # Use "max" for full withdrawal
    asset_decimals: int,
    user_address: str,
) -> Dict[str, Any]:
    """
    Generate complete transaction data for Aave V3 withdraw operation.

    Args:
        pool_address: Aave V3 Pool contract address
        asset_address: Asset to withdraw
        amount: Human-readable amount or "max" for full withdrawal
        asset_decimals: Token decimals
        user_address: User's wallet address

    Returns:
        Transaction dictionary with to, data, value fields
    """
    if amount == "max" or (isinstance(amount, str) and amount.lower() == "max"):
        amount_wei = max_uint256()
    else:
        amount_wei = wei_from_decimal(amount, asset_decimals)

    calldata = encode_withdraw_calldata(
        asset_address=asset_address,
        amount_wei=amount_wei,
        to_address=user_address,
    )

    return {
        "to": pool_address,
        "data": calldata,
        "value": "0",
        "gas_limit": "300000",  # Estimated gas limit
    }
