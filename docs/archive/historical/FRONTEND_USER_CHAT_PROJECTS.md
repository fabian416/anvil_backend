# FRONTEND_USER_CHAT_PROJECTS

## User Chat Projects Module

**User Type:** Authenticated User  
**Module:** AI Chat - Project Selection & Specialized Contexts  
**Route:** `/chat/projects`, `/chat` (with project context)  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**AI Chat Projects** - Specialized DeFi Assistance with Context-Aware Intelligence

### Description
Project-based chat system that provides users with specialized AI assistance tailored to specific DeFi use cases. Each project has custom branding, focused knowledge, enabled tools, and risk configurations.

### Key Capabilities
- ✅ 10 pre-configured DeFi projects
- ✅ Project selection with visual branding
- ✅ Context-aware AI responses
- ✅ Project-specific knowledge bases
- ✅ Customized tool access per project
- ✅ Risk configurations per project
- ✅ Auto-assignment based on portfolio
- ✅ Multi-project support (users can be in multiple projects)
- ✅ Project switching with context preservation

---

## 🎨 **10 AVAILABLE PROJECTS**

| Icon | Project | Focus | Target User |
|------|---------|-------|-------------|
| 💰 | **Smart Savings** | Low-risk stablecoin yields | Conservative investors |
| 🌾 | **Yield Farming** | Active farming & LP | Yield seekers |
| 🏦 | **Aave Lending** | Complete Aave assistance | Aave users |
| 📈 | **DeFi Trading** | Spot & perp trading | Active traders |
| 🥩 | **Staking Hub** | ETH & LST staking | Stakers |
| 🌉 | **Cross-Chain Bridge** | Multi-chain transfers | Multi-chain users |
| 📊 | **Portfolio Manager** | Portfolio optimization | Portfolio managers |
| 🗳️ | **DAO Governance** | Voting & delegation | DAO participants |
| 🛡️ | **Risk Management** | Hedging & protection | Risk-averse users |
| 🎨 | **NFT Finance** | NFT collateral & lending | NFT holders |

---

## 👤 User Stories

### US-USER-PROJECTS-001: Discover Relevant Projects
**As a** user  
**I want to** see which projects are available and relevant to me  
**So that** I can find specialized assistance for my needs

**Acceptance Criteria:**
- Projects displayed with icons, names, descriptions
- "Recommended for you" section based on portfolio
- Public projects shown to all users
- Private/invite-only projects shown if assigned

---

### US-USER-PROJECTS-002: Select Active Project
**As a** user  
**I want to** select which project I'm currently working in  
**So that** I get specialized assistance for that use case

**Acceptance Criteria:**
- One-tap project selection
- Visual confirmation of active project
- Project context loads seamlessly
- Welcome message displays
- Enabled tools/chains shown

---

### US-USER-PROJECTS-003: Switch Between Projects
**As a** user  
**I want to** easily switch between my assigned projects  
**So that** I can get different types of assistance as needed

**Acceptance Criteria:**
- Quick project switcher accessible
- Current project always visible
- Smooth context transition
- Conversation history preserved per project
- Visual branding updates immediately

---

### US-USER-PROJECTS-004: Auto-Assignment on Onboarding
**As a** new user  
**I want to** be automatically assigned to relevant projects  
**So that** I don't have to configure everything manually

**Acceptance Criteria:**
- Auto-assignment runs after onboarding
- Based on portfolio analysis
- Based on stated goals
- User can manually add/remove projects
- Notification when auto-assigned

---

## 🖼️ Wireframes

### View 1: Project Selection Screen (Mobile)

```
┌─────────────────────────────────────┐
│  [←]    Select Your Project         │
├─────────────────────────────────────┤
│                                     │
│  Recommended for You                │
│  ┌─────────────────────────────────┐│
│  │  💰  Smart Savings              ││
│  │      Low-risk stablecoin yields ││
│  │      Based on your USDC holdings││
│  │                                 ││
│  │      [Select Project] →         ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  📊  Portfolio Manager          ││
│  │      Track & optimize holdings  ││
│  │      You have 5 protocols       ││
│  │                                 ││
│  │      [Select Project] →         ││
│  └─────────────────────────────────┘│
│                                     │
│  All Available Projects             │
│  ┌───────────────┐ ┌───────────────┐│
│  │  🌾 Earning   │ │  🏦 Aave      ││
│  │               │ │               ││
│  │  [Select]     │ │  [Select]     ││
│  └───────────────┘ └───────────────┘│
│  ┌───────────────┐ ┌───────────────┐│
│  │  📈 Trading   │ │  🥩 Staking   ││
│  │               │ │               ││
│  │  [Select]     │ │  [Select]     ││
│  └───────────────┘ └───────────────┘│
│  ┌───────────────┐ ┌───────────────┐│
│  │  🌉 Bridge    │ │  🗳️ Governance││
│  │               │ │               ││
│  │  [Select]     │ │  [Select]     ││
│  └───────────────┘ └───────────────┘│
│  ┌───────────────┐ ┌───────────────┐│
│  │  🛡️ Risk Mgmt │ │  🎨 NFT       ││
│  │               │ │               ││
│  │  [Select]     │ │  [Select]     ││
│  └───────────────┘ └───────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 2: Chat with Active Project Context (Mobile)

```
┌─────────────────────────────────────┐
│  [☰]  💰 Smart Savings     [Switch] │ ← Active project
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🤖 Welcome to Smart Savings!   ││
│  │                                 ││
│  │     I help you find the best    ││
│  │     low-risk yields for your    ││
│  │     stablecoins.                ││
│  │                                 ││
│  │     I can help you with:        ││
│  │     • Finding best APY          ││
│  │     • Comparing protocols       ││
│  │     • Setting up strategies     ││
│  │     • Understanding risks       ││
│  │                                 ││
│  │     What would you like to      ││
│  │     optimize today?             ││
│  │                          10:30 ││
│  └─────────────────────────────────┘│
│                                     │
│  Quick Actions (Project-Specific)   │
│  ┌─────────────────────────────────┐│
│  │  💵 Best USDC APY               ││
│  │  💰 Compare Aave vs Compound    ││
│  │  📈 Check my positions          ││
│  └─────────────────────────────────┘│
│                                     │
│  Enabled Chains:                    │
│  [Ethereum] [Arbitrum] [Base]       │
│                                     │
│  Enabled Tools:                     │
│  Lend • Portfolio • Health Check    │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  [Type your message...]         ││
│  │                           [Send]││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 3: Project Switcher Modal

```
┌─────────────────────────────────────┐
│  Switch Project                [✕]  │
├─────────────────────────────────────┤
│                                     │
│  Currently Active:                  │
│  ┌─────────────────────────────────┐│
│  │  💰 Smart Savings      ✓ Active││
│  └─────────────────────────────────┘│
│                                     │
│  Your Other Projects:               │
│  ┌─────────────────────────────────┐│
│  │  📊 Portfolio Manager           ││
│  │      Switch to portfolio view   ││
│  │                                 ││
│  │      [Switch to this project]   ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🏦 Aave Lending                ││
│  │      Manage Aave positions      ││
│  │                                 ││
│  │      [Switch to this project]   ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  + Discover More Projects       ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 4: Project Detail (Before Selection)

```
┌─────────────────────────────────────┐
│  [←]    Smart Savings Project       │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────────┐│
│  │         💰                       ││
│  │    SMART SAVINGS                ││
│  │                                 ││
│  │  Low-risk yield optimization    ││
│  │  for stablecoin holdings        ││
│  └─────────────────────────────────┘│
│                                     │
│  What You Get:                      │
│  ┌─────────────────────────────────┐│
│  │  ✓ Expert guidance on stable    ││
│  │    yields across protocols      ││
│  │                                 ││
│  │  ✓ Risk-first approach to       ││
│  │    maximize safety              ││
│  │                                 ││
│  │  ✓ Real-time APY comparisons    ││
│  │                                 ││
│  │  ✓ Gas-optimized strategies     ││
│  └─────────────────────────────────┘│
│                                     │
│  Enabled Features:                  │
│  • Protocols: Aave, Compound,       │
│    Morpho, Yearn                    │
│  • Chains: Ethereum, Arbitrum, Base │
│  • Max Position: $100,000           │
│  • Risk Level: Conservative         │
│                                     │
│  Your Portfolio Match:              │
│  ┌─────────────────────────────────┐│
│  │  🎯 Great Match!                ││
│  │  You have $45K in USDC          ││
│  │  This project is perfect for    ││
│  │  optimizing stablecoin yields.  ││
│  └─────────────────────────────────┘│
│                                     │
│  [Join This Project]                │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Integration

### Get User's Projects

```typescript
// GET /api/v1/projects/
interface UserProjectsResponse {
  assigned_projects: ProjectSummary[];
  active_project_id: string | null;
}

interface ProjectSummary {
  id: string;
  slug: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  welcome_message: string;
  is_featured: boolean;
}
```

### Activate Project

```typescript
// POST /api/v1/projects/:project_id/activate
const activateProject = async (projectId: string) => {
  const response = await api.post(
    `/api/v1/projects/${projectId}/activate`
  );
  return response.data;
};
```

### List Available Projects

```typescript
// GET /api/v1/projects/available
const getAvailableProjects = async (): Promise<ProjectSummary[]> => {
  const response = await api.get('/api/v1/projects/available');
  return response.data;
};
```

---

## 🎨 Motion Design

### Project Selection Animation (Framer Motion)

```typescript
import { motion } from 'framer-motion';

function ProjectCard({ project, onSelect }: ProjectCardProps) {
  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -4 }}
      whileTap={{ scale: 0.98 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ borderColor: project.color }}
      className="border-2 rounded-xl p-4 cursor-pointer"
      onClick={() => onSelect(project)}
    >
      <div className="text-4xl mb-2">{project.icon}</div>
      <h3 className="font-bold text-lg">{project.name}</h3>
      <p className="text-sm text-gray-600">{project.description}</p>
      
      <motion.button
        whileHover={{ x: 4 }}
        className="mt-3 text-blue-600 flex items-center gap-1"
      >
        Select Project →
      </motion.button>
    </motion.div>
  );
}
```

### Project Switch Animation

```typescript
function ChatWithProject({ activeProject }: ChatProps) {
  return (
    <div>
      {/* Project header with color transition */}
      <motion.div
        animate={{
          backgroundColor: activeProject.color,
        }}
        transition={{ duration: 0.6, ease: 'easeInOut' }}
        className="p-4 text-white"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{activeProject.icon}</span>
            <span className="font-bold">{activeProject.name}</span>
          </div>
          <button onClick={openProjectSwitcher}>Switch</button>
        </div>
      </motion.div>
      
      {/* Chat messages with context indicator */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeProject.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          transition={{ duration: 0.3 }}
        >
          <ChatMessages />
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
```

### Context Loading State

```typescript
function ProjectContextLoader({ project }: { project: Project }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg"
    >
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
        className="text-2xl"
      >
        {project.icon}
      </motion.div>
      <div>
        <p className="font-semibold">Loading {project.name} context...</p>
        <p className="text-sm text-gray-600">
          Preparing specialized assistance
        </p>
      </div>
    </motion.div>
  );
}
```

---

## 🎨 React Native Motion (Reanimated)

### Project Card Animation

```typescript
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
} from 'react-native-reanimated';

function ProjectCardNative({ project, onSelect }: ProjectCardProps) {
  const scale = useSharedValue(1);
  const pressed = useSharedValue(0);
  
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [
      { scale: scale.value },
      { translateY: withSpring(pressed.value ? -8 : 0) },
    ],
  }));
  
  const handlePressIn = () => {
    scale.value = withSpring(0.95);
    pressed.value = 1;
  };
  
  const handlePressOut = () => {
    scale.value = withSpring(1);
    pressed.value = 0;
  };
  
  return (
    <Animated.View style={[styles.card, animatedStyle]}>
      <Pressable
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        onPress={() => onSelect(project)}
      >
        <Text style={styles.icon}>{project.icon}</Text>
        <Text style={styles.name}>{project.name}</Text>
        <Text style={styles.description}>{project.description}</Text>
      </Pressable>
    </Animated.View>
  );
}
```

---

## 📱 Component Specifications

### ProjectSelector Component

```typescript
interface ProjectSelectorProps {
  projects: ProjectSummary[];
  activeProjectId: string | null;
  onSelectProject: (projectId: string) => Promise<void>;
  recommendedProjects?: string[];
}

function ProjectSelector({
  projects,
  activeProjectId,
  onSelectProject,
  recommendedProjects = [],
}: ProjectSelectorProps) {
  const recommended = projects.filter(p => 
    recommendedProjects.includes(p.id)
  );
  const other = projects.filter(p => 
    !recommendedProjects.includes(p.id)
  );
  
  return (
    <div className="space-y-6">
      {recommended.length > 0 && (
        <section>
          <h2 className="text-lg font-bold mb-3">Recommended for You</h2>
          <div className="space-y-3">
            {recommended.map(project => (
              <ProjectCard
                key={project.id}
                project={project}
                isActive={project.id === activeProjectId}
                onSelect={onSelectProject}
              />
            ))}
          </div>
        </section>
      )}
      
      <section>
        <h2 className="text-lg font-bold mb-3">All Projects</h2>
        <div className="grid grid-cols-2 gap-3">
          {other.map(project => (
            <ProjectCard
              key={project.id}
              project={project}
              isActive={project.id === activeProjectId}
              onSelect={onSelectProject}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
```

### ProjectHeader Component

```typescript
interface ProjectHeaderProps {
  project: ProjectSummary;
  onOpenSwitcher: () => void;
}

function ProjectHeader({ project, onOpenSwitcher }: ProjectHeaderProps) {
  return (
    <div
      style={{ backgroundColor: project.color }}
      className="p-4 text-white flex items-center justify-between"
    >
      <div className="flex items-center gap-2">
        <span className="text-2xl">{project.icon}</span>
        <span className="font-bold">{project.name}</span>
      </div>
      <button
        onClick={onOpenSwitcher}
        className="bg-white/20 px-3 py-1 rounded-full text-sm"
      >
        Switch
      </button>
    </div>
  );
}
```

### ProjectContextBadge Component

```typescript
interface ProjectContextBadgeProps {
  project: ProjectSummary;
  size?: 'sm' | 'md' | 'lg';
}

function ProjectContextBadge({ project, size = 'md' }: ProjectContextBadgeProps) {
  const sizes = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-3 py-1.5',
    lg: 'text-base px-4 py-2',
  };
  
  return (
    <div
      style={{
        backgroundColor: `${project.color}20`,
        borderColor: project.color,
      }}
      className={`border-2 rounded-full inline-flex items-center gap-1 ${sizes[size]}`}
    >
      <span>{project.icon}</span>
      <span style={{ color: project.color }} className="font-semibold">
        {project.name}
      </span>
    </div>
  );
}
```

---

## 🔗 React Hooks

### useProjects Hook

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useProjects() {
  const queryClient = useQueryClient();
  
  const { data: projects, isLoading } = useQuery({
    queryKey: ['user-projects'],
    queryFn: async () => {
      const response = await api.get('/api/v1/projects/');
      return response.data;
    },
  });
  
  const activateProject = useMutation({
    mutationFn: async (projectId: string) => {
      await api.post(`/api/v1/projects/${projectId}/activate`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-projects'] });
      queryClient.invalidateQueries({ queryKey: ['chat-context'] });
    },
  });
  
  return {
    projects: projects?.assigned_projects ?? [],
    activeProjectId: projects?.active_project_id,
    isLoading,
    activateProject: activateProject.mutate,
  };
}
```

### useActiveProject Hook

```typescript
export function useActiveProject() {
  const { projects, activeProjectId } = useProjects();
  
  const activeProject = projects.find(p => p.id === activeProjectId);
  
  return {
    activeProject,
    isProjectActive: !!activeProject,
  };
}
```

---

## 🎭 User Flows

### Flow 1: First-Time Project Selection

```
1. User completes onboarding
   ↓
2. System runs auto-assignment rules
   ↓
3. User sees "Select Your Project" screen
   ↓
4. Recommended projects shown first (based on portfolio)
   ↓
5. User taps project card
   ↓
6. Project detail screen shows capabilities
   ↓
7. User confirms selection
   ↓
8. Project context loads with animation
   ↓
9. Welcome message displays
   ↓
10. Chat ready with project-specific assistance
```

### Flow 2: Switching Projects Mid-Session

```
1. User in active chat (e.g., Savings project)
   ↓
2. User taps "Switch" button in header
   ↓
3. Project switcher modal opens
   ↓
4. Shows current project + other assigned projects
   ↓
5. User selects different project (e.g., Aave)
   ↓
6. Confirmation: "Switch to Aave Lending?"
   ↓
7. Context transition animation (color change)
   ↓
8. New project welcome message shows
   ↓
9. Chat history preserved but project context updated
   ↓
10. Tools/chains/protocols updated to new project
```

---

## 🎨 Visual Design Tokens

### Project Color Palette

```typescript
export const PROJECT_COLORS = {
  savings: '#10B981',      // Green
  earning: '#F59E0B',      // Amber
  aave: '#B6509E',         // Aave Purple
  trading: '#3B82F6',      // Blue
  staking: '#8B5CF6',      // Purple
  bridge: '#EC4899',       // Pink
  portfolio: '#06B6D4',    // Cyan
  governance: '#F97316',   // Orange
  risk: '#EF4444',         // Red
  nft_finance: '#A855F7',  // Purple
};
```

### Project Icon Set

```typescript
export const PROJECT_ICONS = {
  savings: '💰',
  earning: '🌾',
  aave: '🏦',
  trading: '📈',
  staking: '🥩',
  bridge: '🌉',
  portfolio: '📊',
  governance: '🗳️',
  risk: '🛡️',
  nft_finance: '🎨',
};
```

---

## 🔧 State Management (Zustand)

```typescript
interface ProjectStore {
  activeProject: ProjectSummary | null;
  assignedProjects: ProjectSummary[];
  isLoading: boolean;
  
  setActiveProject: (project: ProjectSummary) => void;
  loadProjects: () => Promise<void>;
  activateProject: (projectId: string) => Promise<void>;
}

export const useProjectStore = create<ProjectStore>((set, get) => ({
  activeProject: null,
  assignedProjects: [],
  isLoading: false,
  
  setActiveProject: (project) => set({ activeProject: project }),
  
  loadProjects: async () => {
    set({ isLoading: true });
    const response = await api.get('/api/v1/projects/');
    const activeProj = response.data.assigned_projects.find(
      (p: ProjectSummary) => p.id === response.data.active_project_id
    );
    set({
      assignedProjects: response.data.assigned_projects,
      activeProject: activeProj || null,
      isLoading: false,
    });
  },
  
  activateProject: async (projectId) => {
    await api.post(`/api/v1/projects/${projectId}/activate`);
    await get().loadProjects();
  },
}));
```

---

## 🎯 Integration with Chat

### Chat Component Updates

```typescript
function ChatScreen() {
  const { activeProject } = useActiveProject();
  const [projectSwitcherOpen, setProjectSwitcherOpen] = useState(false);
  
  // Show project selection if no active project
  if (!activeProject) {
    return <ProjectSelector />;
  }
  
  return (
    <div>
      <ProjectHeader
        project={activeProject}
        onOpenSwitcher={() => setProjectSwitcherOpen(true)}
      />
      
      {/* Chat interface with project context */}
      <ChatInterface projectContext={activeProject} />
      
      {/* Project switcher modal */}
      <ProjectSwitcherModal
        open={projectSwitcherOpen}
        onClose={() => setProjectSwitcherOpen(false)}
      />
    </div>
  );
}
```

### Message Component with Project Context

```typescript
function AIMessage({ message, project }: MessageProps) {
  return (
    <div className="flex gap-3">
      <div
        style={{ backgroundColor: project.color }}
        className="w-8 h-8 rounded-full flex items-center justify-center text-white"
      >
        {project.icon}
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold">AI Assistant</span>
          <ProjectContextBadge project={project} size="sm" />
        </div>
        <div className="prose">{message.content}</div>
      </div>
    </div>
  );
}
```

---

## ⚠️ Error Handling

```typescript
const projectErrors = {
  PROJ_001: 'Failed to load projects',
  PROJ_002: 'Project not found',
  PROJ_003: 'You do not have access to this project',
  PROJ_004: 'Project is currently inactive',
  PROJ_005: 'Failed to switch projects',
  PROJ_006: 'Project is at capacity',
};

// Handle project selection error
try {
  await activateProject(projectId);
} catch (error) {
  if (error.status === 403) {
    toast.error('You do not have access to this project');
  } else if (error.status === 404) {
    toast.error('Project not found');
  } else {
    toast.error('Failed to activate project. Please try again.');
  }
}
```

---

## ♿ Accessibility

### ARIA Labels

```typescript
<button
  aria-label={`Select ${project.name} project for ${project.description}`}
  role="button"
  onClick={() => onSelect(project)}
>
  <span aria-hidden="true">{project.icon}</span>
  <span>{project.name}</span>
</button>
```

### Keyboard Navigation

```typescript
function ProjectGrid({ projects, onSelect }: ProjectGridProps) {
  const handleKeyPress = (e: KeyboardEvent, project: Project) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(project);
    }
  };
  
  return (
    <div role="grid">
      {projects.map((project, idx) => (
        <div
          key={project.id}
          role="gridcell"
          tabIndex={0}
          onKeyPress={(e) => handleKeyPress(e, project)}
        >
          <ProjectCard project={project} onSelect={onSelect} />
        </div>
      ))}
    </div>
  );
}
```

---

## 🔒 Security

### Project Access Control

```typescript
// Verify user has access before activating
const verifyProjectAccess = async (userId: string, projectId: string) => {
  const { assigned_projects } = await api.get(`/api/v1/projects/`);
  const hasAccess = assigned_projects.some(p => p.id === projectId);
  
  if (!hasAccess) {
    throw new Error('Unauthorized: Project access denied');
  }
};
```

### Project Context Validation

```typescript
// Ensure project context is valid before sending messages
const validateProjectContext = (project: ProjectSummary) => {
  if (!project.id) throw new Error('Invalid project: missing ID');
  if (!project.slug) throw new Error('Invalid project: missing slug');
  
  return true;
};
```

---

## 🧪 Testing

```typescript
describe('ProjectSelector', () => {
  it('displays recommended projects first', () => {
    const { getByText } = render(
      <ProjectSelector 
        projects={mockProjects}
        recommendedProjects={['savings-id']}
      />
    );
    
    expect(getByText('Recommended for You')).toBeInTheDocument();
    expect(getByText('Smart Savings')).toBeInTheDocument();
  });
  
  it('activates project on selection', async () => {
    const onSelect = jest.fn();
    const { getByText } = render(
      <ProjectSelector projects={mockProjects} onSelectProject={onSelect} />
    );
    
    fireEvent.click(getByText('Smart Savings'));
    
    await waitFor(() => {
      expect(onSelect).toHaveBeenCalledWith('savings-id');
    });
  });
});
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Chat Projects*  
*Backend Status: ✅ 100% Implemented*  
*Frontend Status: ⚠️ Needs Implementation*
