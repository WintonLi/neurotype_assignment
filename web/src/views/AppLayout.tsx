import type { FunctionComponent } from "react";
import { useState } from "react";
import type { MenuProps } from "antd";
import { ConfigProvider, Layout, Menu } from "antd";
import { Link, Outlet } from "react-router-dom";
import { DesktopOutlined, PieChartOutlined, CheckOutlined, LogoutOutlined } from "@ant-design/icons";
import { useAssessmentStore } from "../store/assessmentStore";

const { Content, Sider } = Layout;
type MenuItem = Required<MenuProps>["items"][number];

const items: MenuItem[] = [
  {
    key: "1",
    icon: <PieChartOutlined />,
    label: <Link to="/queue">Queue</Link>,
  },
  {
    key: "2",
    icon: <CheckOutlined />,
    label: <Link to="/issued">Issued</Link>,
  },
  {
    key: "3",
    icon: <DesktopOutlined />,
    label: <Link to="/audit">Audit</Link>,
  },
];

interface AppLayoutProps {}

const AppLayout: FunctionComponent<AppLayoutProps> = () => {
  const [collapsed, setCollapsed] = useState(true);
  const username = useAssessmentStore((state) => state.username);
  const logout = useAssessmentStore((state) => state.logout);

  const logoutItems: MenuItem[] = [
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: username ? `Logout (${username})` : "Logout",
      onClick: logout,
    },
  ];

  return (
    <ConfigProvider
      theme={{
        components: {
          Layout: {
            bodyBg: "white",  // Set the background color for the layout body
          },
        },
      }}
    >
      <Layout style={{ minHeight: "100vh" }}>
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={(value) => setCollapsed(value)}
          style={{ display: "flex", flexDirection: "column" }}
        >
          <div className="demo-logo-vertical" />
          <Menu theme="dark" defaultSelectedKeys={["1"]} items={items} style={{ flex: 1 }} />
          <Menu theme="dark" selectable={false} items={logoutItems} />
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

