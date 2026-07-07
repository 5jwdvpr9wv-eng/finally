import type { ConnectionStatus } from '@/lib/types';

const COLORS: Record<ConnectionStatus, string> = {
  connected: 'bg-up-green',
  reconnecting: 'bg-accent-yellow',
  disconnected: 'bg-down-red',
};

const LABELS: Record<ConnectionStatus, string> = {
  connected: 'Connected',
  reconnecting: 'Reconnecting',
  disconnected: 'Disconnected',
};

export function ConnectionDot({ status }: { status: ConnectionStatus }) {
  return (
    <div className="flex items-center gap-2" data-testid="connection-status" data-status={status}>
      <span
        className={`inline-block h-2.5 w-2.5 rounded-full ${COLORS[status]}`}
        aria-hidden="true"
      />
      <span className="text-xs text-gray-400">{LABELS[status]}</span>
    </div>
  );
}
