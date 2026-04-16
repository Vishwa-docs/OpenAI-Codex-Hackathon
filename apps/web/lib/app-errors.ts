export class BackendUnavailableError extends Error {
  sourcePath: string;

  constructor(sourcePath: string, details?: string) {
    super(details ?? `Backend unavailable for ${sourcePath}`);
    this.name = "BackendUnavailableError";
    this.sourcePath = sourcePath;
  }
}

export function isBackendUnavailableError(error: unknown): error is BackendUnavailableError {
  return error instanceof BackendUnavailableError;
}
