import { message } from "antd";
import { AxiosError } from "axios";
import type { ErrorInfo, ReactNode } from "react";
import { Component } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

const showAndLogError = (error: string) => {
  message.error(error, 3); // show the error message on screen
};

const handlePromiseRejection = (event: PromiseRejectionEvent) => {
  /** Generally, all HTTP request errors, if not handled by components, will be here */
  if (event?.reason instanceof AxiosError) {
    const r = event.reason;
    const c = event.reason?.config;
    const errorMessage = `Axio error detected. Message: ${event.reason.message} Code: ${r.code}; Method: ${c?.method}; BaseUrl: ${c?.baseURL}; URL: ${c?.url}`;
    showAndLogError(errorMessage);
    return;
  }
  showAndLogError(JSON.stringify(event.reason, null, 4));
};

const handleUncaughtError = (event: ErrorEvent) => {
  showAndLogError(JSON.stringify(event.message, null, 4));
};

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    window.addEventListener("unhandledrejection", handlePromiseRejection);
    window.addEventListener("error", handleUncaughtError);
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    showAndLogError(error.message);
    // eslint-disable-next-line no-console
    console.error("Uncaught error:", error, errorInfo);
  }

  public componentWillUnmount() {
    window.removeEventListener("unhandledrejection", handlePromiseRejection);
    window.removeEventListener("error", handleUncaughtError);
  }

  public render() {
    const { children } = this.props;
    return <>{children}</>;
  }
}

export default ErrorBoundary;
