"""Educational static responses for common token questions."""
from typing import Dict, Optional

# Static responses for common educational questions about tokens
EDUCATIONAL_RESPONSES: Dict[str, Dict[str, str]] = {
    "en": {
        "bitcoin": """**Bitcoin (BTC)** is the first and largest cryptocurrency by market capitalization.

**Key Features:**
- **Decentralized**: No central authority controls Bitcoin
- **Limited Supply**: Only 21 million Bitcoin will ever exist
- **Blockchain**: Transactions recorded on a public ledger
- **Digital Gold**: Often called "digital gold" due to store of value properties

**Use Cases:**
- Store of value (like gold)
- Peer-to-peer payments
- Remittances (sending money across borders)
- Investment/portfolio diversification

**Current Status**: Bitcoin is the most widely adopted cryptocurrency with millions of users worldwide.

Want to learn more about Bitcoin trading or DeFi? Sign up for full access!""",

        "btc": """**BTC** is the ticker symbol for **Bitcoin**, the first cryptocurrency.

Bitcoin was created in 2009 by an anonymous person (or group) using the name Satoshi Nakamoto. It's a decentralized digital currency that operates without a central bank or single administrator.

**Quick Facts:**
- Symbol: BTC
- Max Supply: 21 million
- Consensus: Proof of Work (PoW)
- Block Time: ~10 minutes

Want to trade Bitcoin or explore DeFi opportunities? Sign up to get started!""",

        "ethereum": """**Ethereum (ETH)** is the second-largest cryptocurrency and the leading platform for decentralized applications (dApps).

**Key Features:**
- **Smart Contracts**: Programmable contracts that execute automatically
- **dApps**: Decentralized applications built on Ethereum
- **DeFi Hub**: Most DeFi protocols run on Ethereum
- **NFTs**: Non-fungible tokens are primarily Ethereum-based

**Use Cases:**
- Running smart contracts
- Building dApps
- DeFi protocols (lending, trading, yield farming)
- NFT creation and trading

**Current Status**: Ethereum has the largest DeFi ecosystem with billions in total value locked (TVL).

Want to explore DeFi on Ethereum? Sign up for full access!""",

        "eth": """**ETH** is the ticker symbol for **Ethereum**, the leading blockchain for decentralized applications.

Ethereum enables developers to build and deploy smart contracts and dApps without downtime, fraud, or third-party interference.

**Quick Facts:**
- Symbol: ETH
- Supply: Unlimited (but issuance is controlled)
- Consensus: Proof of Stake (PoS) since The Merge
- Block Time: ~12 seconds

Want to use Ethereum for DeFi? Sign up to get started!""",

        "defi": """**DeFi (Decentralized Finance)** is a financial system built on blockchain that operates without traditional intermediaries like banks.

**Key Features:**
- **No Intermediaries**: Direct peer-to-peer transactions
- **Open Access**: Anyone with a wallet can participate
- **Transparent**: All transactions are on-chain and verifiable
- **Programmable**: Smart contracts automate financial operations

**Common DeFi Activities:**
- Lending and borrowing (Aave, Compound)
- Trading/swapping (Uniswap, SushiSwap)
- Yield farming (earning rewards for providing liquidity)
- Staking (earning rewards for securing networks)

**Current Status**: DeFi has grown to over $100 billion in total value locked across various protocols.

Want to start using DeFi? Sign up to get started!""",
    },
    "es": {
        "bitcoin": """**Bitcoin (BTC)** es la primera y mayor criptomoneda por capitalización de mercado.

**Características Clave:**
- **Descentralizado**: Ninguna autoridad central controla Bitcoin
- **Suministro Limitado**: Solo existirán 21 millones de Bitcoin
- **Blockchain**: Transacciones registradas en un libro público
- **Oro Digital**: A menudo llamado "oro digital" por sus propiedades de reserva de valor

**Casos de Uso:**
- Reserva de valor (como el oro)
- Pagos peer-to-peer
- Remesas (enviar dinero a través de fronteras)
- Diversificación de inversión/portafolio

¿Quieres aprender más sobre trading de Bitcoin o DeFi? ¡Regístrate para acceso completo!""",

        "btc": """**BTC** es el símbolo de cotización de **Bitcoin**, la primera criptomoneda.

Bitcoin fue creado en 2009 por una persona (o grupo) anónimo usando el nombre Satoshi Nakamoto. Es una moneda digital descentralizada que opera sin un banco central o administrador único.

**Datos Rápidos:**
- Símbolo: BTC
- Suministro Máximo: 21 millones
- Consenso: Proof of Work (PoW)
- Tiempo de Bloque: ~10 minutos

¿Quieres operar Bitcoin o explorar oportunidades DeFi? ¡Regístrate para comenzar!""",

        "ethereum": """**Ethereum (ETH)** es la segunda criptomoneda más grande y la plataforma líder para aplicaciones descentralizadas (dApps).

**Características Clave:**
- **Smart Contracts**: Contratos programables que se ejecutan automáticamente
- **dApps**: Aplicaciones descentralizadas construidas en Ethereum
- **Hub DeFi**: La mayoría de protocolos DeFi funcionan en Ethereum
- **NFTs**: Los tokens no fungibles son principalmente basados en Ethereum

**Casos de Uso:**
- Ejecutar smart contracts
- Construir dApps
- Protocolos DeFi (préstamos, trading, yield farming)
- Creación y trading de NFTs

¿Quieres explorar DeFi en Ethereum? ¡Regístrate para acceso completo!""",

        "eth": """**ETH** es el símbolo de cotización de **Ethereum**, la blockchain líder para aplicaciones descentralizadas.

Ethereum permite a los desarrolladores construir y desplegar smart contracts y dApps sin tiempo de inactividad, fraude o interferencia de terceros.

**Datos Rápidos:**
- Símbolo: ETH
- Suministro: Ilimitado (pero la emisión está controlada)
- Consenso: Proof of Stake (PoS) desde The Merge
- Tiempo de Bloque: ~12 segundos

¿Quieres usar Ethereum para DeFi? ¡Regístrate para comenzar!""",

        "defi": """**DeFi (Finanzas Descentralizadas)** es un sistema financiero construido en blockchain que opera sin intermediarios tradicionales como bancos.

**Características Clave:**
- **Sin Intermediarios**: Transacciones peer-to-peer directas
- **Acceso Abierto**: Cualquiera con una billetera puede participar
- **Transparente**: Todas las transacciones están on-chain y son verificables
- **Programable**: Los smart contracts automatizan operaciones financieras

**Actividades DeFi Comunes:**
- Préstamos y borrowing (Aave, Compound)
- Trading/swapping (Uniswap, SushiSwap)
- Yield farming (ganar recompensas por proporcionar liquidez)
- Staking (ganar recompensas por asegurar redes)

¿Quieres comenzar a usar DeFi? ¡Regístrate para comenzar!""",
    },
    "pt": {
        "bitcoin": """**Bitcoin (BTC)** é a primeira e maior criptomoeda por capitalização de mercado.

**Características Principais:**
- **Descentralizado**: Nenhuma autoridade central controla o Bitcoin
- **Oferta Limitada**: Apenas 21 milhões de Bitcoin existirão
- **Blockchain**: Transações registradas em um livro público
- **Ouro Digital**: Frequentemente chamado de "ouro digital" devido às propriedades de reserva de valor

**Casos de Uso:**
- Reserva de valor (como ouro)
- Pagamentos peer-to-peer
- Remessas (enviar dinheiro através de fronteiras)
- Diversificação de investimento/portfólio

Quer aprender mais sobre trading de Bitcoin ou DeFi? Cadastre-se para acesso completo!""",

        "btc": """**BTC** é o símbolo de negociação de **Bitcoin**, a primeira criptomoeda.

Bitcoin foi criado em 2009 por uma pessoa (ou grupo) anônimo usando o nome Satoshi Nakamoto. É uma moeda digital descentralizada que opera sem um banco central ou administrador único.

**Fatos Rápidos:**
- Símbolo: BTC
- Oferta Máxima: 21 milhões
- Consenso: Proof of Work (PoW)
- Tempo de Bloco: ~10 minutos

Quer negociar Bitcoin ou explorar oportunidades DeFi? Cadastre-se para começar!""",

        "ethereum": """**Ethereum (ETH)** é a segunda maior criptomoeda e a plataforma líder para aplicações descentralizadas (dApps).

**Características Principais:**
- **Smart Contracts**: Contratos programáveis que executam automaticamente
- **dApps**: Aplicações descentralizadas construídas no Ethereum
- **Hub DeFi**: A maioria dos protocolos DeFi funcionam no Ethereum
- **NFTs**: Tokens não fungíveis são principalmente baseados em Ethereum

**Casos de Uso:**
- Executar smart contracts
- Construir dApps
- Protocolos DeFi (empréstimos, trading, yield farming)
- Criação e trading de NFTs

Quer explorar DeFi no Ethereum? Cadastre-se para acesso completo!""",

        "eth": """**ETH** é o símbolo de negociação de **Ethereum**, a blockchain líder para aplicações descentralizadas.

Ethereum permite que desenvolvedores construam e implantem smart contracts e dApps sem tempo de inatividade, fraude ou interferência de terceiros.

**Fatos Rápidos:**
- Símbolo: ETH
- Oferta: Ilimitada (mas a emissão é controlada)
- Consenso: Proof of Stake (PoS) desde The Merge
- Tempo de Bloco: ~12 segundos

Quer usar Ethereum para DeFi? Cadastre-se para começar!""",

        "defi": """**DeFi (Finanças Descentralizadas)** é um sistema financeiro construído em blockchain que opera sem intermediários tradicionais como bancos.

**Características Principais:**
- **Sem Intermediários**: Transações peer-to-peer diretas
- **Acesso Aberto**: Qualquer pessoa com uma carteira pode participar
- **Transparente**: Todas as transações estão on-chain e são verificáveis
- **Programável**: Smart contracts automatizam operações financeiras

**Atividades DeFi Comuns:**
- Empréstimos e borrowing (Aave, Compound)
- Trading/swapping (Uniswap, SushiSwap)
- Yield farming (ganhar recompensas por fornecer liquidez)
- Staking (ganhar recompensas por proteger redes)

Quer começar a usar DeFi? Cadastre-se para começar!""",
    },
    "zh": {
        "bitcoin": """**比特币 (BTC)** 是按市值计算的第一大和最大的加密货币。

**主要特点:**
- **去中心化**: 没有中央机构控制比特币
- **有限供应**: 只有2100万比特币将存在
- **区块链**: 交易记录在公共账本上
- **数字黄金**: 由于价值存储属性，通常被称为"数字黄金"

**用例:**
- 价值存储（如黄金）
- 点对点支付
- 汇款（跨境汇款）
- 投资/投资组合多元化

想了解更多关于比特币交易或DeFi的信息？注册以获得完整访问权限！""",

        "btc": """**BTC** 是**比特币**的交易代码，这是第一种加密货币。

比特币由匿名人士（或团体）于2009年创建，使用中本聪这个名字。它是一种去中心化的数字货币，在没有中央银行或单一管理员的情况下运行。

**快速事实:**
- 符号: BTC
- 最大供应量: 2100万
- 共识: 工作量证明 (PoW)
- 区块时间: ~10分钟

想交易比特币或探索DeFi机会？注册开始吧！""",
    },
}


def get_educational_response(token: str, language: str = "en") -> Optional[str]:
    """
    Get educational static response for a token.
    
    Args:
        token: Token symbol or name (e.g., "BTC", "bitcoin", "ETH")
        language: Language code (en, es, pt, zh)
    
    Returns:
        Educational response text or None if not available
    """
    # Normalize token to lowercase
    token_lower = token.lower()
    
    # Get responses for language
    lang_responses = EDUCATIONAL_RESPONSES.get(language, EDUCATIONAL_RESPONSES["en"])
    
    # Try exact match first
    if token_lower in lang_responses:
        return lang_responses[token_lower]
    
    # Try common variations
    token_variations = {
        "bitcoin": "bitcoin",
        "btc": "btc",
        "ethereum": "ethereum",
        "eth": "eth",
        "defi": "defi",
        "decentralized finance": "defi",
    }
    
    normalized_token = token_variations.get(token_lower, token_lower)
    if normalized_token in lang_responses:
        return lang_responses[normalized_token]
    
    # Fallback to English if not found in requested language
    if language != "en":
        en_responses = EDUCATIONAL_RESPONSES.get("en", {})
        if token_lower in en_responses:
            return en_responses[token_lower]
        if normalized_token in en_responses:
            return en_responses[normalized_token]
    
    return None
