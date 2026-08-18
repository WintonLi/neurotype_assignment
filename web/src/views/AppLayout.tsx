import type { FunctionComponent } from "react";
import { useState } from "react";
import type { MenuProps } from "antd";
import { ConfigProvider, Layout, Menu } from "antd";
import { Link, Outlet } from "react-router-dom";
import { DesktopOutlined, PieChartOutlined } from "@ant-design/icons";

const { Content, Sider } = Layout;
type MenuItem = Required<MenuProps>["items"][number];

const items: MenuItem[] = [
  {
    key: "1",
    icon: <PieChartOutlined />,
    label: <Link to="/assessment">Assessment</Link>,
  },
  {
    key: "2",
    icon: <DesktopOutlined />,
    label: <Link to="/audit">Audit</Link>,
  },
];

interface AppLayoutProps {}

const AppLayout: FunctionComponent<AppLayoutProps> = () => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <ConfigProvider
      theme={{
        components: {
          Layout: {
            bodyBg: "#f0f2f5",  // Set the background color for the layout body
          },
        },
      }}
    >
      <Layout style={{ minHeight: "100vh" }}>
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={(value) => setCollapsed(value)}
        >
          <div className="demo-logo-vertical" />
          <Menu theme="dark" defaultSelectedKeys={["1"]} items={items} />
        </Sider>
        <Layout>
          <Content style={{ margin: "0 20px" }}>
            <Outlet />
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
};

export default AppLayout;
