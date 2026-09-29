export class ApiError extends Error {
  constructor(
    public status: number,
    public field: string,
    public reason: string,
    public article?: unknown
  ) {
    super(reason)
  }
  body() {
    return {
      errors: { [this.field]: [this.reason] },
      ...(this.article ? { article: this.article } : {}),
    }
  }
}
export const missing = () => new ApiError(401, 'token', 'is missing')
export const absent = (field: string) => new ApiError(404, field, 'not found')
export const forbidden = (field: string) => new ApiError(403, field, 'forbidden')
export const invalid = (field: string, reason = 'is invalid') => new ApiError(422, field, reason)
