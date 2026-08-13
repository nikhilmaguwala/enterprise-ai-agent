type ErrorBannerProps = {
  title?: string;
  message: string;
  onRetry?: () => void;
};

export function ErrorBanner({
  title = "Something went wrong",
  message,
  onRetry,
}: ErrorBannerProps) {
  return (
    <div
      role="alert"
      className="rounded-lg border border-error-container bg-error-container/40 px-4 py-3 text-sm text-danger"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-medium">{title}</p>
          <p className="mt-1 opacity-90">{message}</p>
        </div>
        {onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            className="shrink-0 rounded-md border border-error-container bg-surface px-3 py-1.5 text-xs font-medium text-danger hover:bg-error-container/30"
          >
            Retry
          </button>
        ) : null}
      </div>
    </div>
  );
}
