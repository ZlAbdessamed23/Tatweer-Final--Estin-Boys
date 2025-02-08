
export class CustomError extends Error {
    constructor(
      public message: string,
      public statusCode: number,
      public errorCode?: string,
      public details?: string
    ) {
      super(message);
      this.name = this.constructor.name;
      Error.captureStackTrace(this, this.constructor);
    }
  }
  
  export class ValidationError extends CustomError {
    constructor(message: string, details?: string) {
      super(message, 400, "VALIDATION_ERROR", details);
    }
  }
  
  export class NotFoundError extends CustomError {
    constructor(message: string) {
      super(message, 404, "NOT_FOUND");
    }
  }
  
  export class UnauthorizedError extends CustomError {
    constructor(message: string) {
      super(message, 401, "UNAUTHORIZED");
    }
  }
  
  export class DatabaseError extends CustomError {
    constructor(message: string, details?: string) {
      super(message, 500, "DATABASE_ERROR", details);
    }
  }
  
  export class InternalServerError extends CustomError {
    constructor(message: string) {
      super(message, 500, "INTERNAL_SERVER_ERROR");
    }
  }
  export class AccountNotActivatedError extends CustomError {
    constructor(message: string) {
      super(message, 403, "ACCOUNT_NOT_ACTIVATED");
    }
  }
  export class VerificationError extends CustomError {
    constructor(message: string, statusCode: number) {
      super(message, statusCode, "VERIFICATION_ERROR");
    }
  }
  
  // New error classes
  
  export class PaymentError extends CustomError {
    constructor(message: string, details?: string) {
      super(message, 402, "PAYMENT_ERROR", details);
    }
  }
  
  export class ForbiddenError extends CustomError {
    constructor(message: string) {
      super(message, 403, "FORBIDDEN");
    }
  }
  
  export class ConflictError extends CustomError {
    constructor(message: string, details?: string) {
      super(message, 409, "CONFLICT", details);
    }
  }
  export class LimitExceededError extends CustomError {
    constructor(message: string, details?: string) {
      super(message, 429, "LIMIT_EXCEEDED", details);
    }
  }
  export class RateLimitError extends CustomError {
    constructor(message: string) {
      super(message, 429, "RATE_LIMIT_EXCEEDED");
    }
  }
  
  export class BadGatewayError extends CustomError {
    constructor(message: string) {
      super(message, 502, "BAD_GATEWAY");
    }
  }
  
  export class ServiceUnavailableError extends CustomError {
    constructor(message: string) {
      super(message, 503, "SERVICE_UNAVAILABLE");
    }
  }
  
  export class TimeoutError extends CustomError {
    constructor(message: string) {
      super(message, 504, "GATEWAY_TIMEOUT");
    }
  }
  
  export class AuthenticationError extends CustomError {
    constructor(message: string) {
      super(message, 401, "AUTHENTICATION_FAILED");
    }
  }
  
  export class SubscriptionError extends Error {
    public redirectUrl?: string;
  
    constructor(message: string, options?: { redirectUrl: string }) {
      super(message);
      this.name = "SubscriptionError";
      this.redirectUrl = options?.redirectUrl;
    }
  }
  
  export class DataIntegrityError extends CustomError {
    constructor(message: string, details?: string) {
      super(message, 422, "DATA_INTEGRITY_ERROR", details);
    }
  }