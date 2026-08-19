import type { FunctionComponent } from "react";
import { useEffect, useState } from "react";
import { Alert, Card, Col, Input, Row, Select, Table, Tag } from "antd";
import type { ColumnsType, TablePaginationConfig } from "antd/es/table";
import type {
  AuditAction,
  AuditChange,
  AuditEntityType,
  AuditEvent,
} from "../services/auditService";
import { listAuditEvents } from "../services/auditService";

const ACTIONS: AuditAction[] = ["view", "create", "update", "issue", "deactivate"];
const ENTITY_TYPES: AuditEntityType[] = ["assessment", "user"];

const ACTION_COLORS: Record<AuditAction, string> = {
  view: "blue",
  create: "green",
  update: "gold",
  issue: "purple",
  deactivate: "red",
};

const renderChanges = (changes: AuditChange[]) => (
  <>
    {changes.map((change) => (
      <div key={change.field}>
        <Tag>{change.field}</Tag>
        {String(change.before)} → {String(change.after)}
      </div>
    ))}
  </>
);

const columns: ColumnsType<AuditEvent> = [
  {
    title: "Occurred At",
    dataIndex: "occurred_at",
    render: (value: string) => new Date(value).toLocaleString(),
  },
  {
    title: "Actor",
    dataIndex: "actor",
    render: (actor: AuditEvent["actor"]) => actor.display_name,
  },
  {
    title: "Action",
    dataIndex: "action",
    render: (value: AuditAction) => <Tag color={ACTION_COLORS[value]}>{value}</Tag>,
  },
  { title: "Entity Type", dataIndex: "entity_type" },
  { title: "Entity", dataIndex: "entity_id" },
  {
    title: "Changes",
    dataIndex: "changes",
    render: (changes: AuditChange[]) => (changes.length > 0 ? renderChanges(changes) : "-"),
  },
];

interface AuditProps {}

const Audit: FunctionComponent<AuditProps> = () => {
  const [entityType, setEntityType] = useState<AuditEntityType | undefined>(undefined);
  const [entityId, setEntityId] = useState<string | undefined>(undefined);
  const [actorId, setActorId] = useState<string | undefined>(undefined);
  const [action, setAction] = useState<AuditAction | undefined>(undefined);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const [items, setItems] = useState<AuditEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    listAuditEvents({
      entity_type: entityType,
      entity_id: entityId,
      actor_id: actorId,
      action,
      page,
      page_size: pageSize,
    })
      .then((response) => {
        if (cancelled) return;
        setItems(response.items);
        setTotal(response.total);
      })
      .catch((err: Error) => {
        if (cancelled) return;
        setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [entityType, entityId, actorId, action, page, pageSize]);

  const handleTableChange = (pagination: TablePaginationConfig) => {
    setPage(pagination.current ?? 1);
    setPageSize(pagination.pageSize ?? 20);
  };

  return (
    <Card title="Audit Events">
      <Row gutter={8} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Select
            allowClear
            placeholder="Entity Type"
            style={{ width: "100%" }}
            value={entityType}
            onChange={(value) => {
              setPage(1);
              setEntityType(value);
            }}
            options={ENTITY_TYPES.map((value) => ({ label: value, value }))}
          />
        </Col>
        <Col span={6}>
          <Input
            allowClear
            placeholder="Entity ID"
            value={entityId}
            onChange={(event) => {
              setPage(1);
              setEntityId(event.target.value || undefined);
            }}
          />
        </Col>
        <Col span={6}>
          <Input
            allowClear
            placeholder="Actor"
            value={actorId}
            onChange={(event) => {
              setPage(1);
              setActorId(event.target.value || undefined);
            }}
          />
        </Col>
        <Col span={6}>
          <Select
            allowClear
            placeholder="Action"
            style={{ width: "100%" }}
            value={action}
            onChange={(value) => {
              setPage(1);
              setAction(value);
            }}
            options={ACTIONS.map((value) => ({ label: value, value }))}
          />
        </Col>
      </Row>
      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}
      <Table<AuditEvent>
        rowKey="id"
        columns={columns}
        dataSource={items}
        loading={loading}
        pagination={{ current: page, pageSize, total, showSizeChanger: true }}
        onChange={handleTableChange}
      />
    </Card>
  );
};

export default Audit;

