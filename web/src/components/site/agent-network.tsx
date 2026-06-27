import Image from "next/image";
import { agents, type Agent } from "@/lib/content";

// Node coordinates (in %) evenly distributed on a circle around the core.
const COORDS: Record<Agent["position"], { x: number; y: number }> = {
  top: { x: 50, y: 10 },
  "top-right": { x: 78, y: 23 },
  right: { x: 90, y: 50 },
  "bottom-right": { x: 78, y: 75 },
  bottom: { x: 50, y: 88 },
  "bottom-left": { x: 22, y: 75 },
  left: { x: 10, y: 50 },
  "top-left": { x: 22, y: 23 },
};

export function AgentNetwork() {
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[560px]">
      {/* Connectors + platform (behind everything) */}
      <svg
        viewBox="0 0 100 100"
        className="absolute inset-0 h-full w-full"
        aria-hidden
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <filter id="lineGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="0.6" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <radialGradient id="floor" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgb(255 106 0 / 0.18)" />
            <stop offset="100%" stopColor="rgb(255 106 0 / 0)" />
          </radialGradient>
        </defs>

        {/* Hexagonal "Casper Network" platform */}
        <polygon
          points="50,60 84,71 84,83 50,94 16,83 16,71"
          fill="url(#floor)"
          stroke="rgb(255 106 0 / 0.35)"
          strokeWidth="0.4"
        />
        <polygon
          points="50,66 73,73 73,80 50,87 27,80 27,73"
          fill="none"
          stroke="rgb(255 106 0 / 0.18)"
          strokeWidth="0.3"
        />

        {/* Connector lines from core to each node */}
        <g filter="url(#lineGlow)">
          {agents.map((agent) => {
            const { x, y } = COORDS[agent.position];
            return (
              <line
                key={agent.label}
                x1="50"
                y1="50"
                x2={x}
                y2={y}
                stroke="rgb(255 106 0 / 0.45)"
                strokeWidth="0.4"
                strokeDasharray="1 1.4"
                strokeLinecap="round"
              />
            );
          })}
        </g>
      </svg>

      {/* Slowly rotating orbit ring */}
      <div className="pointer-events-none absolute left-1/2 top-1/2 size-[62%] -translate-x-1/2 -translate-y-1/2 animate-orbit rounded-full border border-dashed border-brand/20" />

      {/* Central reactor core */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
        <div className="pointer-events-none absolute left-1/2 top-1/2 size-48 -translate-x-1/2 -translate-y-1/2 brand-glow" />
        <div className="animate-core relative flex size-28 items-center justify-center rounded-full border border-brand/40 bg-[radial-gradient(circle_at_50%_35%,#241206,#0a0a0a)] shadow-[0_0_70px_-8px_rgb(255_106_0_/_0.7)] sm:size-32">
          <div className="absolute inset-1.5 rounded-full border border-brand/15" />
          <div className="absolute inset-0 rounded-full ring-1 ring-inset ring-white/5" />
          <Image
            src="/images/logos/agentmesh/AgentMesh_App_Icon_Orange.png"
            alt="AgentMesh core"
            width={64}
            height={64}
            className="size-12 drop-shadow-[0_0_12px_rgb(255_106_0_/_0.8)] sm:size-14"
          />
        </div>
      </div>

      {/* Agent nodes */}
      {agents.map((agent) => {
        const { x, y } = COORDS[agent.position];
        const Icon = agent.icon;
        return (
          <div
            key={agent.label}
            className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-2"
            style={{ left: `${x}%`, top: `${y}%` }}
          >
            <span className="relative inline-flex size-12 items-center justify-center rounded-2xl border border-white/10 bg-gradient-to-b from-[#1d1d1d] to-[#0b0b0b] text-brand shadow-[0_10px_24px_-8px_rgba(0,0,0,0.9)] sm:size-[52px]">
              <span className="absolute inset-x-2 top-0 h-px bg-white/15" />
              <Icon className="size-5 sm:size-[22px]" strokeWidth={1.75} />
            </span>
            <div className="text-center leading-tight">
              <div className="whitespace-nowrap text-[10px] font-semibold uppercase tracking-wide text-foreground">
                {agent.label}
              </div>
              <div className="text-[9px] uppercase tracking-wider text-brand/70">
                Agent
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
