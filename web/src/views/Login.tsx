import type { FunctionComponent } from "react";
import { Navigate } from "react-router-dom";
import { Alert, Button, Card, Flex, Form, Input, Typography } from "antd";
import { useAssessmentStore } from "../store/assessmentStore";

const { Title } = Typography;

interface LoginFormValues {
  username: string;
  password: string;
}

const Login: FunctionComponent = () => {
  const username = useAssessmentStore((state) => state.username);
  const login = useAssessmentStore((state) => state.login);

  // Already logged in: bounce straight to the app.
  if (username) {
    return <Navigate to="/queue" replace />;
  }

  const handleFinish = (values: LoginFormValues) => {
    login(values.username.trim());
  };

  return (
    <Flex justify="center" align="center" style={{ minHeight: "100vh" }}>
      <Card style={{ width: 360 }}>
        <Title level={3} style={{ textAlign: "center" }}>
          Sign in
        </Title>
        <Alert
          type="info"
          showIcon
          message={
            <>
              Use <b>test</b> (clinician) or <b>reviewer</b> (reviewer) as the username.
            </>
          }
          style={{ marginBottom: 16 }}
        />
        <Form<LoginFormValues> layout="vertical" onFinish={handleFinish}>
          <Form.Item
            label="Username"
            name="username"
            rules={[{ required: true, message: "Username is required" }]}
          >
            <Input placeholder="test or reviewer" autoFocus />
          </Form.Item>
          <Form.Item
            label="Password"
            name="password"
            rules={[{ required: true, message: "Password is required" }]}
          >
            <Input.Password placeholder="Password" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" block>
              Log in
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </Flex>
  );
};

export default Login;
