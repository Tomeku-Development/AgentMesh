import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";

type LogoProps = {
  className?: string;
  /** White wordmark by default; "orange" for accent contexts. */
  variant?: "white" | "orange";
  width?: number;
  height?: number;
};

const sources: Record<NonNullable<LogoProps["variant"]>, string> = {
  white: "/images/logos/agentmesh/AgentMesh_Wordmark_White_RGB.png",
  orange: "/images/logos/agentmesh/AgentMesh_Wordmark_Orange_RGB.png",
};

export function Logo({
  className,
  variant = "white",
  width = 150,
  height = 30,
}: LogoProps) {
  return (
    <Link
      href="/"
      aria-label="AgentMesh home"
      className={cn("inline-flex items-center", className)}
    >
      <Image
        src={sources[variant]}
        alt="AgentMesh"
        width={width}
        height={height}
        priority
        className="h-7 w-auto"
      />
    </Link>
  );
}
