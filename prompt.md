iUSER API USE CASES
1. Authentication & Session Management
Use CaseAPI EndpointDescriptionLogin via PrivyPOST /user/auth/loginAuthenticate via email, wallet, or social (Google)Refresh TokenPOST /user/auth/refreshRenew access token using refresh tokenLogoutPOST /user/auth/logoutInvalidate session and tokensHandle Banned User-Block access with AUTH_USER_BANNEDKYC Required Flow-Enforce KYC with AUTH_KYC_REQUIRED

2. Profile Management
Use CaseAPI EndpointDescriptionGet ProfileGET /user/profileRetrieve user profile with wallets, tier, KYC statusUpdate ProfilePUT /user/profileChange username, avatar, risk profileHandle Username Conflict-PROFILE_USERNAME_TAKEN error

3. Wallet Management (Multi-Chain)
Use CaseAPI EndpointDescriptionAdd WalletPOST /user/wallets/addLink new wallet with signature verificationRemove WalletDELETE /user/wallets/{wallet_id}Remove non-primary walletVerify Wallet Ownership-Signature verification on addPrevent Primary Wallet Removal-WALLET_IS_PRIMARY errorEnforce Wallet Limit-WALLET_LIMIT_REACHED error

4. DeFi Transaction Execution
Use CaseAPI EndpointDescriptionExecute TransactionPOST /user/transactions/executeSubmit swap/borrow/stake with risk assessmentSimulate TransactionPOST /user/transactions/simulateDry-run without executionVerify TransactionPOST /user/transactions/{id}/verifySign with Privy or walletGet Transaction HistoryGET /user/transactionsFilter by status, chain, type, dateGet Transaction DetailsGET /user/transactions/{id}Full audit trail, simulation, risk dataHandle High Risk Abort-TX_RISK_TOO_HIGH blocks risky txsHandle Insufficient Balance-TX_INSUFFICIENT_BALANCE errorHandle Failed Simulation-TX_SIMULATION_FAILED errorHandle Gas Too High-TX_GAS_TOO_HIGH protectionHandle Blocked Contract-TX_CONTRACT_BLOCKED for blacklisted
Transaction Types Supported:

swap - Token swaps via DEX (Uniswap, 1inch)
provide_liquidity / remove_liquidity - LP positions
borrow / repay - Lending (AAVE, Morpho)
stake / unstake - Staking operations
claim_rewards - Yield harvesting


5. AI Chat & Agent Interaction
Use CaseAPI EndpointDescriptionSend MessagePOST /user/chat/messageQuery AI agents with contextList Chat SessionsGET /user/chat/sessionsView conversation historyGet Session MessagesGET /user/chat/sessions/{session_id}/messagesLoad specific conversationHandle Rate Limit-CHAT_RATE_LIMIT throttlingHandle Token Quota-CHAT_TOKEN_LIMIT for usage capAgent Unavailable-AGENT_UNAVAILABLE fallback
Agents Available:

SwapAgent - DEX aggregation, quote comparison
TradingAgent - Perpetual futures (Hyperliquid)
PortfolioAgent - Holdings tracking, analytics
Researcher - Market analysis, opportunities
Risk Analyzer - Position evaluation


6. Portfolio Management
Use CaseAPI EndpointDescriptionGet PortfolioGET /user/portfolioConsolidated view across chainsFilter by Chain?chain_id=1Chain-specific positionsInclude History?include_history=trueHistorical value trackingView Lending Positions-AAVE, Morpho, Compound dataView LP Positions-Uniswap V3, fees, IL tracking

7. Risk Management
Use CaseAPI EndpointDescriptionGet Risk ScoreGET /user/risk/scoreCurrent risk metrics + factorsGet Risk ConfigGET /user/risk/configUser preferences + global defaultsUpdate Risk ConfigPOST /user/risk/configSet slippage, limits, protectionsEnable MEV Protection-Flag in risk configSet Allowed Protocols-Whitelist for transactions

8. Alerts & Notifications
Use CaseAPI EndpointDescriptionSubscribe to AlertsPOST /user/alerts/subscribePrice, risk, news alertsGet Alert HistoryGET /user/alertsPast triggered alertsConfigure Thresholds-Price change %, risk score limitsSet Channels-Webhook, email delivery

9. Analytics & Insights
Use CaseAPI EndpointDescriptionGet AnalyticsGET /user/analyticsPersonal performance dataTransaction Summary-Volume, success rate, feesPortfolio Performance-Returns, max value trackingAI Usage Stats-Tokens consumed, satisfaction

10. Real-Time WebSocket Events
Event TypeUse Casetransaction.updateTrack tx confirmation statusportfolio.updateReal-time balance changesalert.riskRisk threshold breach warningsalert.newsMarket sentiment updatesagent.messageStreaming AI responses

👨‍💼 ADMIN API USE CASES
1. User Administration
Use CaseAPI EndpointPermissionList UsersGET /admin/usersusers.readSearch Users?search=wallet/emailusers.readFilter by Status?status=bannedusers.readGet User DetailsGET /admin/users/{id}users.readModify UserPUT /admin/users/{id}users.writeBan/Unban User-users.writeChange Subscription Tier-users.writeUpdate KYC Status-users.write

2. Role & Permission Management
Use CaseAPI EndpointPermissionAssign Admin RolePOST /admin/users/{id}/rolesroles.writeRevoke Admin RoleDELETE /admin/users/{id}/roles/{role_id}roles.writeSet Role Expiration-roles.writeDefine Granular Permissions-roles.write
Role Types:

system_admin - Full platform access
risk_admin - Risk configuration control
support_admin - User/transaction support
viewer - Read-only analytics


3. Transaction Monitoring
Use CaseAPI EndpointPermissionList All TransactionsGET /admin/transactionstransactions.readFilter by Risk Score?risk_score_min=70transactions.readFilter by User?user_id=uuidtransactions.readGet Transaction AuditGET /admin/transactions/{id}/auditaudit.readView Verification Attempts-audit.readView Simulation Results-audit.read

4. Risk Configuration (Platform-Wide)
Use CaseAPI EndpointPermissionUpdate Global Risk ConfigPUT /admin/risk/configrisk.config.writeSet Slippage Limits-risk.config.writeSet Gas Price Limits-risk.config.writeBlock Tokens-risk.config.writeEmergency Pause-risk.config.writeGet Risk ScoresGET /admin/risk/scoresrisk.readUpdate Protocol RiskPOST /admin/risk/protocols/{id}risk.protocols.write

5. AI Agent Management
Use CaseAPI EndpointPermissionList AgentsGET /admin/agentsagents.readView Agent PerformanceGET /admin/agents/{id}/performanceagents.readUpdate Agent ConfigPUT /admin/agents/{id}/configagents.writeChange Model Provider-agents.writeSet Rate Limits-agents.writeMonitor Costs-agents.read

6. Platform Analytics
Use CaseAPI EndpointPermissionView DashboardGET /admin/analytics/dashboardanalytics.readUser Metrics-Active users, signups, tiersTransaction Metrics-Volume, success rate, gas spentAI Usage Metrics-Tokens, costs, popular agentsRevenue Metrics-MRR, transaction fees

7. Audit & Compliance
Use CaseAPI EndpointPermissionView Audit LogsGET /admin/audit/logsaudit.readFilter by Action Type?action_type=user.updatedaudit.readFilter by Admin?admin_id=uuidaudit.readGenerate Compliance ReportGET /admin/reports/compliancecompliance.readKYC Statistics-compliance.readTransaction Monitoring Report-compliance.read

8. Alert Broadcasting
Use CaseAPI EndpointPermissionSend Platform AlertPOST /admin/alerts/broadcastalerts.writeTarget User Groupsall, premium, affectedalerts.writeSet Priority Levelinfo, warning, criticalalerts.writeSpecify Affected Services-alerts.write

📊 SUMMARY STATISTICS
CategoryUser Use CasesAdmin Use CasesAuthentication5-Profile/User Mgmt38Wallet5-Transactions116AI Chat65Portfolio5-Risk66Alerts42Analytics46WebSocket5-Roles-4Audit/Compliance-6TOTAL5443
This gives you 97 total use cases to cover across the User and Admin APIs for complete platform functionality.
