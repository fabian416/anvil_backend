# ULTRA Flash Loan Contracts

Smart contracts for executing flash loans with arbitrage.

## Contracts

| Contract | Protocol | Fee | Description |
|----------|----------|-----|-------------|
| `FlashLoanReceiver.sol` | Aave V3 | 0.09% | Standard flash loan receiver |
| `BalancerFlashLoanReceiver` | Balancer | 0% | Zero-fee flash loans |

## Setup

### 1. Install Dependencies

```bash
cd contracts
npm init -y
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
npm install @aave/v3-core @openzeppelin/contracts
```

### 2. Initialize Hardhat

```bash
npx hardhat init
# Select "Create a JavaScript project"
```

### 3. Configure Hardhat

Edit `hardhat.config.js`:

```javascript
require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.19",
  networks: {
    hardhat: {
      forking: {
        url: "https://eth-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY",
      },
    },
    mainnet: {
      url: "https://eth-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY",
      accounts: [process.env.PRIVATE_KEY],
    },
    arbitrum: {
      url: "https://arb-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY",
      accounts: [process.env.PRIVATE_KEY],
    },
  },
};
```

### 4. Create Deploy Script

Create `scripts/deploy.js`:

```javascript
const hre = require("hardhat");

async function main() {
  // Aave V3 Pool Addresses Provider
  const POOL_ADDRESSES_PROVIDER = {
    mainnet: "0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e",
    arbitrum: "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb",
    optimism: "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb",
    base: "0xe20fCBdBfFC4Dd138cE8b2E6FBb6CB49777ad64D",
    polygon: "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb",
  };

  const network = hre.network.name;
  const provider = POOL_ADDRESSES_PROVIDER[network] || POOL_ADDRESSES_PROVIDER.mainnet;

  console.log(`Deploying to ${network}...`);
  console.log(`Using Pool Addresses Provider: ${provider}`);

  // Deploy Aave Flash Loan Receiver
  const FlashLoanReceiver = await hre.ethers.getContractFactory("FlashLoanReceiver");
  const receiver = await FlashLoanReceiver.deploy(provider);
  await receiver.waitForDeployment();

  console.log(`FlashLoanReceiver deployed to: ${await receiver.getAddress()}`);

  // Deploy Balancer Flash Loan Receiver
  const BalancerReceiver = await hre.ethers.getContractFactory("BalancerFlashLoanReceiver");
  const balancer = await BalancerReceiver.deploy();
  await balancer.waitForDeployment();

  console.log(`BalancerFlashLoanReceiver deployed to: ${await balancer.getAddress()}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
```

### 5. Deploy

```bash
# Test on local fork first
npx hardhat run scripts/deploy.js

# Deploy to mainnet (costs real ETH!)
PRIVATE_KEY=0x... npx hardhat run scripts/deploy.js --network mainnet
```

## Usage

### Execute Flash Loan from Python

```python
from app.application.ultra.flash_loan_executor import FlashLoanExecutor

# After deploying, update the receiver address
RECEIVER_ADDRESS = "0x..."  # Your deployed contract

executor = FlashLoanExecutor(
    alchemy_api_key="your-key",
    chain=Chain.ETHEREUM
)

# Execute flash loan
result = await executor.execute_flash_loan(
    protocol=FlashLoanProtocol.AAVE_V3,
    token="USDC",
    amount=Decimal("100000"),
    receiver=RECEIVER_ADDRESS,
)
```

## Deployment Costs

| Chain | Estimated Gas | Cost (at 30 Gwei) |
|-------|--------------|-------------------|
| Ethereum | ~2M gas | ~$180 |
| Arbitrum | ~2M gas | ~$1-2 |
| Optimism | ~2M gas | ~$1-2 |
| Base | ~2M gas | ~$1-2 |

**Recommendation**: Deploy on Arbitrum first (cheaper), test, then deploy on Ethereum.

## Security Notes

⚠️ **IMPORTANT**:
1. Never commit your private key
2. Test thoroughly on fork before mainnet
3. Start with small amounts
4. Add proper access controls
5. Consider using a multisig for production

## Flash Loan Fees

| Protocol | Fee |
|----------|-----|
| Aave V3 | 0.09% |
| Balancer | 0.00% |
| Uniswap V3 | 0.00% |

**Balancer is best for cost** (0% fee, only gas).
