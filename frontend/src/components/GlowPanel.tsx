import type { ReactNode } from "react";

type GlowPanelProps = {
  children: ReactNode;
  className?: string;
};

export function GlowPanel({ children, className = "" }: GlowPanelProps) {
  return <section className={`glow-panel ${className}`.trim()}>{children}</section>;
}
