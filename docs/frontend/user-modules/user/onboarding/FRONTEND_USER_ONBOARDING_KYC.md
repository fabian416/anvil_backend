# FRONTEND_USER_ONBOARDING_KYC

## User KYC Module

**User Type:** Authenticated User  
**Module:** KYC Verification  
**Route:** `/kyc`, `/settings/kyc`  
**Platform:** Mobile (React Native) & Web

---

## 📋 Module Overview

### Title
**KYC Verification** - Identity Verification Flow

### Description
Know Your Customer verification flow for users to verify their identity, unlocking higher transaction limits and full platform features.

---

## 🖼️ Views & Wireframes

### View 1: KYC Start

```
┌─────────────────────────────────────┐
│  [←]    Verify Your Identity       │
│                                     │
│  ┌─────────────────────────────────┐│
│  │         ┌───────┐               ││
│  │         │  🪪   │               ││
│  │         └───────┘               ││
│  │                                 ││
│  │    Unlock Full Access           ││
│  │                                 ││
│  │  Verify your identity to:       ││
│  │                                 ││
│  │  ✓ Increase transaction limits  ││
│  │  ✓ Access advanced DeFi features││
│  │  ✓ Enable fiat on/off ramp     ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  What you'll need:                  │
│  ┌─────────────────────────────────┐│
│  │  📄 Government-issued ID        ││
│  │     Passport, Driver's License, ││
│  │     or National ID              ││
│  │                                 ││
│  │  📷 Camera access               ││
│  │     For document photos and     ││
│  │     selfie verification         ││
│  └─────────────────────────────────┘│
│                                     │
│  ⏱️ Takes about 3-5 minutes        │
│                                     │
│  ┌─────────────────────────────────┐│
│  │        Start Verification       ││
│  └─────────────────────────────────┘│
│                                     │
│  Your data is encrypted and handled│
│  according to our Privacy Policy.  │
│                                     │
└─────────────────────────────────────┘
```

### View 2: Document Selection

```
┌─────────────────────────────────────┐
│  [←]    Select Document            │
│                                     │
│  Choose your ID type                │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🛂 Passport                    ││
│  │     International travel document││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🚗 Driver's License            ││
│  │     Government-issued license   ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🪪 National ID Card            ││
│  │     Government-issued ID card   ││
│  └─────────────────────────────────┘│
│                                     │
│                                     │
│  Select your issuing country        │
│  ┌─────────────────────────────────┐│
│  │ 🇺🇸 United States           [▼] ││
│  └─────────────────────────────────┘│
│                                     │
│                                     │
└─────────────────────────────────────┘
```

### View 3: Document Capture

```
┌─────────────────────────────────────┐
│  [←]    Scan Front of ID           │
│                                     │
│  ┌─────────────────────────────────┐│
│  │                                 ││
│  │                                 ││
│  │    ┌─────────────────────────┐  ││
│  │    │                         │  ││
│  │    │    [Camera Viewfinder]  │  ││
│  │    │                         │  ││
│  │    │  ┌─────────────────┐    │  ││
│  │    │  │                 │    │  ││
│  │    │  │  Position your  │    │  ││
│  │    │  │  ID here        │    │  ││
│  │    │  │                 │    │  ││
│  │    │  └─────────────────┘    │  ││
│  │    │                         │  ││
│  │    └─────────────────────────┘  ││
│  │                                 ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Tips:                              │
│  • Use good lighting               │
│  • Avoid glare and shadows         │
│  • Keep all corners visible        │
│                                     │
│  ┌─────────────────────────────────┐│
│  │         📷 Capture              ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### View 4: Selfie Capture

```
┌─────────────────────────────────────┐
│  [←]       Take a Selfie           │
│                                     │
│  ┌─────────────────────────────────┐│
│  │                                 ││
│  │    ┌─────────────────────────┐  ││
│  │    │                         │  ││
│  │    │    [Front Camera]       │  ││
│  │    │                         │  ││
│  │    │       ┌───────┐         │  ││
│  │    │       │       │         │  ││
│  │    │       │  😊   │         │  ││
│  │    │       │       │         │  ││
│  │    │       └───────┘         │  ││
│  │    │    Position your face   │  ││
│  │    │                         │  ││
│  │    └─────────────────────────┘  ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Tips:                              │
│  • Look directly at the camera     │
│  • Remove glasses if possible      │
│  • Ensure your face is well-lit    │
│                                     │
│  ┌─────────────────────────────────┐│
│  │         📷 Capture              ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### View 5: Verification Complete

```
┌─────────────────────────────────────┐
│                                     │
│  ┌─────────────────────────────────┐│
│  │         ┌───────┐               ││
│  │         │  ✅   │               ││
│  │         └───────┘               ││
│  │                                 ││
│  │    Verification Submitted!      ││
│  │                                 ││
│  │  We're reviewing your documents.││
│  │  This usually takes a few       ││
│  │  minutes.                       ││
│  │                                 ││
│  │  We'll notify you once your     ││
│  │  verification is complete.      ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Status: ⏳ Under Review        ││
│  │                                 ││
│  │  Submitted: Dec 1, 2025 10:32 AM││
│  │  Est. Time: 5-10 minutes        ││
│  └─────────────────────────────────┘│
│                                     │
│                                     │
│  ┌─────────────────────────────────┐│
│  │         Continue to App         ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

```typescript
// GET /api/users/me/kyc
interface GetKYCStatusResponse {
  success: true;
  data: {
    status: 'not_started' | 'pending' | 'approved' | 'rejected';
    tier?: 'tier_1' | 'tier_2';
    submitted_at?: string;
    reviewed_at?: string;
    rejection_reason?: string;
  };
}

// POST /api/users/me/kyc/start
interface StartKYCResponse {
  success: true;
  data: {
    session_id: string;
    provider_url?: string;
  };
}

// POST /api/users/me/kyc/documents
interface UploadDocumentRequest {
  session_id: string;
  document_type: 'passport' | 'drivers_license' | 'national_id';
  front_image: string; // base64
  back_image?: string; // base64
  selfie_image: string; // base64
  country: string;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 2, 2025*  
*Module: KYC Verification*
