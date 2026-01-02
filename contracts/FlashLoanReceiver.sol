// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@aave/v3-core/contracts/flashloan/base/FlashLoanSimpleReceiverBase.sol";
import "@aave/v3-core/contracts/interfaces/IPoolAddressesProvider.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title FlashLoanReceiver
 * @notice Receives Aave V3 flash loans and executes arbitrage
 * @dev Deploy this contract, then call executeFlashLoan()
 * 
 * DEPLOYMENT:
 * 1. Install dependencies: npm install @aave/v3-core @openzeppelin/contracts
 * 2. Compile: npx hardhat compile
 * 3. Deploy: npx hardhat run scripts/deploy.js --network mainnet
 * 
 * POOL ADDRESSES PROVIDER:
 * - Ethereum: 0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e
 * - Arbitrum: 0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb
 * - Optimism: 0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb
 * - Base: 0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D
 * - Polygon: 0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb
 */
contract FlashLoanReceiver is FlashLoanSimpleReceiverBase {
    address public owner;
    
    // Events
    event FlashLoanExecuted(
        address indexed asset,
        uint256 amount,
        uint256 premium,
        uint256 profit
    );
    
    event ArbitrageExecuted(
        address indexed tokenIn,
        address indexed tokenOut,
        uint256 amountIn,
        uint256 amountOut
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor(address _addressProvider) 
        FlashLoanSimpleReceiverBase(IPoolAddressesProvider(_addressProvider)) 
    {
        owner = msg.sender;
    }

    /**
     * @notice Execute a flash loan
     * @param asset Token to borrow
     * @param amount Amount to borrow
     * @param params Encoded arbitrage parameters
     */
    function executeFlashLoan(
        address asset,
        uint256 amount,
        bytes calldata params
    ) external onlyOwner {
        // Request flash loan from Aave
        POOL.flashLoanSimple(
            address(this),  // receiver
            asset,          // asset to borrow
            amount,         // amount
            params,         // params passed to executeOperation
            0               // referral code
        );
    }

    /**
     * @notice Called by Aave after receiving the flash loan
     * @dev This is where you implement your arbitrage logic
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        require(msg.sender == address(POOL), "Caller must be pool");
        require(initiator == address(this), "Initiator must be this contract");

        // Decode params (customize based on your needs)
        (
            address router1,      // DEX to buy
            address router2,      // DEX to sell
            address tokenOut,     // Intermediate token
            uint256 minProfit     // Minimum profit required
        ) = abi.decode(params, (address, address, address, uint256));

        // ============================================
        // ARBITRAGE LOGIC - CUSTOMIZE THIS
        // ============================================
        
        uint256 balanceBefore = IERC20(asset).balanceOf(address(this));
        
        // Step 1: Approve router1 to spend borrowed tokens
        IERC20(asset).approve(router1, amount);
        
        // Step 2: Swap on DEX 1 (e.g., Uniswap)
        // uint256 amountOut = _swapOnDex(router1, asset, tokenOut, amount);
        
        // Step 3: Approve router2 to spend intermediate tokens
        // IERC20(tokenOut).approve(router2, amountOut);
        
        // Step 4: Swap back on DEX 2 (e.g., SushiSwap)
        // uint256 finalAmount = _swapOnDex(router2, tokenOut, asset, amountOut);
        
        // For now, just check we can repay (no actual arbitrage)
        uint256 balanceAfter = IERC20(asset).balanceOf(address(this));
        
        // ============================================
        // END ARBITRAGE LOGIC
        // ============================================

        // Calculate profit
        uint256 amountOwed = amount + premium;
        require(balanceAfter >= amountOwed, "Insufficient funds to repay");
        
        uint256 profit = balanceAfter - amountOwed;
        require(profit >= minProfit, "Profit below minimum");

        // Approve Aave to pull the owed amount
        IERC20(asset).approve(address(POOL), amountOwed);

        emit FlashLoanExecuted(asset, amount, premium, profit);

        return true;
    }

    /**
     * @notice Withdraw tokens (profits) from contract
     */
    function withdraw(address token, uint256 amount) external onlyOwner {
        IERC20(token).transfer(owner, amount);
    }

    /**
     * @notice Withdraw ETH from contract
     */
    function withdrawETH() external onlyOwner {
        payable(owner).transfer(address(this).balance);
    }

    /**
     * @notice Update owner
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid address");
        owner = newOwner;
    }

    // Receive ETH
    receive() external payable {}
}


/**
 * @title BalancerFlashLoanReceiver
 * @notice Receives Balancer flash loans (0% fee!)
 */
interface IBalancerVault {
    function flashLoan(
        address recipient,
        address[] memory tokens,
        uint256[] memory amounts,
        bytes memory userData
    ) external;
}

contract BalancerFlashLoanReceiver {
    address public owner;
    address public constant BALANCER_VAULT = 0xBA12222222228d8Ba445958a75a0704d566BF2C8;

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /**
     * @notice Execute a Balancer flash loan (0% fee!)
     */
    function executeFlashLoan(
        address[] calldata tokens,
        uint256[] calldata amounts,
        bytes calldata userData
    ) external onlyOwner {
        IBalancerVault(BALANCER_VAULT).flashLoan(
            address(this),
            tokens,
            amounts,
            userData
        );
    }

    /**
     * @notice Called by Balancer after receiving the flash loan
     */
    function receiveFlashLoan(
        address[] memory tokens,
        uint256[] memory amounts,
        uint256[] memory feeAmounts,
        bytes memory userData
    ) external {
        require(msg.sender == BALANCER_VAULT, "Caller must be Balancer");

        // ============================================
        // ARBITRAGE LOGIC - CUSTOMIZE THIS
        // ============================================
        
        // Your arbitrage code here...
        
        // ============================================
        // END ARBITRAGE LOGIC
        // ============================================

        // Repay the flash loan (Balancer has 0% fee!)
        for (uint256 i = 0; i < tokens.length; i++) {
            uint256 amountOwed = amounts[i] + feeAmounts[i];
            IERC20(tokens[i]).transfer(BALANCER_VAULT, amountOwed);
        }
    }

    function withdraw(address token, uint256 amount) external onlyOwner {
        IERC20(token).transfer(owner, amount);
    }

    receive() external payable {}
}
