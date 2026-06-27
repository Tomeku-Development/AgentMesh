import {
  Share2,
  ShieldCheck,
  Zap,
  Boxes,
  CircleDot,
  Search,
  Scale,
  Wallet,
  Fingerprint,
  BarChart3,
  ShieldAlert,
  Users,
  Building2,
  Landmark,
  FileSearch,
  Coins,
  Gavel,
  Network,
  type LucideIcon,
} from "lucide-react";

export const GITHUB_URL = "https://github.com";

/* ------------------------------------------------------------------ */
/* Navigation                                                          */
/* ------------------------------------------------------------------ */

export type NavLink = {
  label: string;
  href: string;
  description?: string;
  external?: boolean;
};

export type NavEntry =
  | { label: string; href: string; items?: never }
  | { label: string; items: NavLink[]; href?: never };

export const navMenus: NavEntry[] = [
  {
    label: "Platform",
    items: [
      {
        label: "Overview",
        href: "/platform",
        description: "How the AgentMesh platform fits together.",
      },
      {
        label: "Multi-Agent Mesh",
        href: "/platform/multi-agent-mesh",
        description: "Specialized agents that collaborate and reach consensus.",
      },
      {
        label: "On-Chain Trust",
        href: "/platform/on-chain-trust",
        description: "Verifiable execution and audit trails on Casper.",
      },
      {
        label: "Pricing",
        href: "/pricing",
        description: "Plans for builders, teams, and enterprises.",
      },
    ],
  },
  { label: "Solutions", href: "/solutions" },
  { label: "Agents", href: "/agents" },
  {
    label: "Developers",
    items: [
      {
        label: "Documentation",
        href: "/docs",
        description: "Guides, concepts, and quickstarts.",
      },
      {
        label: "API Reference",
        href: "/docs/api",
        description: "REST endpoints and contracts.",
      },
      {
        label: "SDKs",
        href: "/sdks",
        description: "Client libraries for your stack.",
      },
      {
        label: "GitHub",
        href: GITHUB_URL,
        description: "Source, examples, and issues.",
        external: true,
      },
    ],
  },
  {
    label: "Company",
    items: [
      { label: "About", href: "/about", description: "Our mission and team." },
      { label: "Blog", href: "/blog", description: "Product news and writing." },
      {
        label: "Careers",
        href: "/careers",
        description: "Help build autonomous organizations.",
      },
      {
        label: "Contact",
        href: "/contact",
        description: "Talk to the team.",
      },
    ],
  },
  { label: "Docs", href: "/docs" },
];

/* ------------------------------------------------------------------ */
/* Features / steps / agents (shared with the landing page)            */
/* ------------------------------------------------------------------ */

export type Feature = {
  icon: LucideIcon;
  title: string;
  description: string;
};

export const features: Feature[] = [
  {
    icon: Share2,
    title: "Multi-Agent Collaboration",
    description:
      "Specialized agents with unique skills collaborate to achieve superior outcomes.",
  },
  {
    icon: ShieldCheck,
    title: "On-Chain Trust",
    description:
      "Every decision and action is recorded on Casper for full transparency and auditability.",
  },
  {
    icon: Zap,
    title: "Autonomous Execution",
    description:
      "Agents can execute transactions, manage funds, and interact with smart contracts.",
  },
  {
    icon: Boxes,
    title: "Modular Architecture",
    description: "Build, deploy, and plug in new agents and skills with ease.",
  },
  {
    icon: CircleDot,
    title: "Built for the Agent Economy",
    description:
      "Payments, reputation, and coordination designed for agents, not humans.",
  },
];

export type Step = {
  number: string;
  title: string;
  description: string;
};

export const steps: Step[] = [
  {
    number: "01",
    title: "You submit a request",
    description: "Define your goal and provide the necessary context.",
  },
  {
    number: "02",
    title: "Agents collaborate",
    description:
      "The mesh of specialized agents analyzes and reasons together.",
  },
  {
    number: "03",
    title: "Consensus is reached",
    description: "Agents debate, vote, and reach an agreement.",
  },
  {
    number: "04",
    title: "Actions are executed",
    description: "Decisions are executed on-chain through Casper.",
  },
];

export type Agent = {
  label: string;
  icon: LucideIcon;
  position:
    | "top"
    | "top-right"
    | "right"
    | "bottom-right"
    | "bottom"
    | "bottom-left"
    | "left"
    | "top-left";
};

export const agents: Agent[] = [
  { label: "Coordinator", icon: Users, position: "top" },
  { label: "Legal", icon: Scale, position: "top-right" },
  { label: "Treasury", icon: Wallet, position: "right" },
  { label: "Audit", icon: Fingerprint, position: "bottom-right" },
  { label: "Execution", icon: Zap, position: "bottom" },
  { label: "Analytics", icon: BarChart3, position: "bottom-left" },
  { label: "Risk", icon: ShieldAlert, position: "left" },
  { label: "Research", icon: Search, position: "top-left" },
];

/* Detailed agent roster used on /agents */
export type AgentDetail = {
  name: string;
  icon: LucideIcon;
  role: string;
  responsibilities: string[];
};

export const agentRoster: AgentDetail[] = [
  {
    name: "Coordinator",
    icon: Users,
    role: "Orchestration",
    responsibilities: [
      "Routes goals to the right specialists",
      "Manages workflow state",
      "Aggregates findings for consensus",
    ],
  },
  {
    name: "Research",
    icon: Search,
    role: "Discovery",
    responsibilities: [
      "Gathers market and external evidence",
      "Summarizes sources with citations",
      "Surfaces relevant context",
    ],
  },
  {
    name: "Finance",
    icon: BarChart3,
    role: "Analysis",
    responsibilities: [
      "Evaluates numbers and runway",
      "Models scenarios",
      "Flags financial risk",
    ],
  },
  {
    name: "Legal",
    icon: Scale,
    role: "Compliance",
    responsibilities: [
      "Reviews structure and terms",
      "Checks regulatory exposure",
      "Documents legal rationale",
    ],
  },
  {
    name: "Risk",
    icon: ShieldAlert,
    role: "Assurance",
    responsibilities: [
      "Scores downside and exposure",
      "Identifies failure modes",
      "Recommends mitigations",
    ],
  },
  {
    name: "Treasury",
    icon: Wallet,
    role: "Execution",
    responsibilities: [
      "Executes approved transactions",
      "Enforces spending limits",
      "Manages on-chain funds",
    ],
  },
  {
    name: "Audit",
    icon: Fingerprint,
    role: "Verification",
    responsibilities: [
      "Records immutable audit trail",
      "Verifies execution integrity",
      "Enables third-party review",
    ],
  },
  {
    name: "Execution",
    icon: Zap,
    role: "Action",
    responsibilities: [
      "Interacts with smart contracts",
      "Carries out approved actions",
      "Confirms on-chain settlement",
    ],
  },
];

/* ------------------------------------------------------------------ */
/* Solutions (/solutions)                                              */
/* ------------------------------------------------------------------ */

export type Solution = {
  icon: LucideIcon;
  title: string;
  description: string;
};

export const solutions: Solution[] = [
  {
    icon: Landmark,
    title: "Venture Due Diligence",
    description:
      "An autonomous investment committee that analyzes, debates, and records verdicts on-chain.",
  },
  {
    icon: Wallet,
    title: "Treasury Management",
    description:
      "Policy-bound agents that manage funds and execute transactions within strict limits.",
  },
  {
    icon: Gavel,
    title: "DAO Governance",
    description:
      "Proposal analysis, voting, and execution your members can independently verify.",
  },
  {
    icon: ShieldCheck,
    title: "Compliance Automation",
    description:
      "Reasoning workflows with an immutable, auditable decision trail for regulated contexts.",
  },
  {
    icon: FileSearch,
    title: "Real-World Asset Verification",
    description:
      "Agent workflows that verify and attest to off-chain assets with on-chain proof.",
  },
  {
    icon: Coins,
    title: "Autonomous Procurement",
    description:
      "Agents that source, evaluate, and settle for services using x402 payments.",
  },
];

/* ------------------------------------------------------------------ */
/* Pricing (/pricing)                                                  */
/* ------------------------------------------------------------------ */

export type PricingTier = {
  name: string;
  price: string;
  cadence?: string;
  description: string;
  features: string[];
  cta: { label: string; href: string };
  highlighted?: boolean;
};

export const pricingTiers: PricingTier[] = [
  {
    name: "Sandbox",
    price: "Free",
    description: "For builders exploring the platform on Casper Testnet.",
    features: [
      "Casper Testnet access",
      "Core agent roster",
      "Limited monthly workflow runs",
      "Community support",
    ],
    cta: { label: "Start building", href: "/contact" },
  },
  {
    name: "Pro",
    price: "$99",
    cadence: "/mo",
    description: "For teams shipping real multi-agent workflows.",
    features: [
      "Everything in Sandbox",
      "Custom organizations & roles",
      "Workflow builder",
      "Higher run limits",
      "Priority support",
    ],
    cta: { label: "Get early access", href: "/contact" },
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    description: "For organizations with compliance and scale needs.",
    features: [
      "Everything in Pro",
      "SSO & advanced permissions",
      "Casper Mainnet deployment",
      "Audit & compliance controls",
      "Dedicated support & SLAs",
    ],
    cta: { label: "Talk to sales", href: "/contact" },
  },
];

export type Faq = { question: string; answer: string };

export const pricingFaqs: Faq[] = [
  {
    question: "Do I need a database to try AgentMesh?",
    answer:
      "No. The platform runs against Casper Testnet in the Sandbox tier. AI usage is billed transparently as you scale.",
  },
  {
    question: "How are AI costs handled?",
    answer:
      "Model usage (OpenAI, Anthropic, Gemini) is passed through transparently. Infrastructure scales with agent activity, not seats.",
  },
  {
    question: "Can I bring my own agents?",
    answer:
      "Yes. The agent SDK lets you publish and install custom agents. A marketplace is on the roadmap.",
  },
  {
    question: "Is human oversight required?",
    answer:
      "Critical or irreversible actions are gated by human approval. You delegate execution while keeping control.",
  },
];

/* ------------------------------------------------------------------ */
/* Developers — SDKs (/sdks) & Docs hub (/docs)                        */
/* ------------------------------------------------------------------ */

export type Sdk = {
  name: string;
  language: string;
  install: string;
  status: "Stable" | "Beta" | "Planned";
};

export const sdks: Sdk[] = [
  {
    name: "TypeScript SDK",
    language: "TypeScript / Node",
    install: "npm install @agentmesh/sdk",
    status: "Beta",
  },
  {
    name: "Python SDK",
    language: "Python 3.11+",
    install: "pip install agentmesh",
    status: "Beta",
  },
  {
    name: "Casper Tools",
    language: "Odra / Casper SDK",
    install: "cargo add agentmesh-casper",
    status: "Planned",
  },
];

export type DocSection = {
  icon: LucideIcon;
  title: string;
  description: string;
  href: string;
};

export const docSections: DocSection[] = [
  {
    icon: Boxes,
    title: "Quickstart",
    description: "Create your first organization and run a workflow.",
    href: "/docs",
  },
  {
    icon: Network,
    title: "Concepts",
    description: "Agents, the mesh, consensus, and on-chain execution.",
    href: "/platform/multi-agent-mesh",
  },
  {
    icon: ShieldCheck,
    title: "On-Chain Trust",
    description: "How decisions are recorded and verified on Casper.",
    href: "/platform/on-chain-trust",
  },
  {
    icon: FileSearch,
    title: "API Reference",
    description: "Endpoints, payloads, and authentication.",
    href: "/docs/api",
  },
];

/* ------------------------------------------------------------------ */
/* Company                                                             */
/* ------------------------------------------------------------------ */

export type Value = { icon: LucideIcon; title: string; description: string };

export const companyValues: Value[] = [
  {
    icon: ShieldCheck,
    title: "Trust First",
    description: "Verifiable execution before scale. Always.",
  },
  {
    icon: Network,
    title: "Open by Default",
    description: "Developer adoption and open standards drive the platform.",
  },
  {
    icon: Building2,
    title: "Built for Real Work",
    description: "Depth on trust-sensitive workflows over shallow breadth.",
  },
];

export type BlogPost = {
  slug: string;
  title: string;
  excerpt: string;
  date: string;
  category: string;
  readingTime: string;
};

export const blogPosts: BlogPost[] = [
  {
    slug: "introducing-agentmesh",
    title: "Introducing AgentMesh",
    excerpt:
      "Why the future of organizations is autonomous, and how a mesh of specialized agents gets us there.",
    date: "2026-01-12",
    category: "Announcements",
    readingTime: "5 min",
  },
  {
    slug: "on-chain-trust-on-casper",
    title: "On-Chain Trust on Casper",
    excerpt:
      "Separating off-chain reasoning from on-chain trust — and why it matters for autonomous decisions.",
    date: "2026-01-26",
    category: "Engineering",
    readingTime: "7 min",
  },
  {
    slug: "the-agent-economy",
    title: "The Agent Economy",
    excerpt:
      "How x402 payments and reputation enable agents to transact with each other autonomously.",
    date: "2026-02-09",
    category: "Vision",
    readingTime: "6 min",
  },
];

export type Job = {
  title: string;
  team: string;
  location: string;
  type: string;
};

export const jobOpenings: Job[] = [
  {
    title: "Senior Full-Stack Engineer",
    team: "Platform",
    location: "Remote",
    type: "Full-time",
  },
  {
    title: "AI / Agent Engineer",
    team: "Agents",
    location: "Remote",
    type: "Full-time",
  },
  {
    title: "Smart Contract Engineer (Casper)",
    team: "Protocol",
    location: "Remote",
    type: "Full-time",
  },
  {
    title: "Product Designer",
    team: "Design",
    location: "Remote",
    type: "Full-time",
  },
];

/* ------------------------------------------------------------------ */
/* Footer                                                              */
/* ------------------------------------------------------------------ */

export const footer = {
  columns: [
    {
      title: "Platform",
      links: [
        { label: "Overview", href: "/platform" },
        { label: "Multi-Agent Mesh", href: "/platform/multi-agent-mesh" },
        { label: "On-Chain Trust", href: "/platform/on-chain-trust" },
        { label: "Pricing", href: "/pricing" },
      ],
    },
    {
      title: "Developers",
      links: [
        { label: "Documentation", href: "/docs" },
        { label: "API Reference", href: "/docs/api" },
        { label: "SDKs", href: "/sdks" },
        { label: "GitHub", href: GITHUB_URL, external: true },
      ],
    },
    {
      title: "Company",
      links: [
        { label: "About", href: "/about" },
        { label: "Blog", href: "/blog" },
        { label: "Careers", href: "/careers" },
        { label: "Contact", href: "/contact" },
      ],
    },
  ],
  legal: [
    { label: "Privacy", href: "/privacy" },
    { label: "Terms", href: "/terms" },
    { label: "Status", href: "/status" },
  ],
};
