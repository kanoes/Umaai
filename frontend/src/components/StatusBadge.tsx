type StatusBadgeProps = {
  status: string;
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const tone =
    status === "success"
      ? "ok"
      : status === "error"
        ? "danger"
        : status === "running"
          ? "live"
          : "idle";

  return <span className={`status-badge ${tone}`}>{status}</span>;
}
