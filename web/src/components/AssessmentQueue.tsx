import type { FunctionComponent } from "react";
import { useEffect, useState } from "react";
import { Alert, Card, Col, Input, Row, Select, Table, Tag } from "antd";
import type { ColumnsType, TablePaginationConfig } from "antd/es/table";
import type {
  AssessmentListItem,
  DomainName,
  DomainResult,
  SupportNeedBand,
} from "../services/assessmentService";
import { listAssessments } from "../services/assessmentService";

const DOMAINS: DomainName[] = [
  "social_communication",
  "sensory_processing",
  "executive_function",
  "emotional_regulation",
  "motor_coordination",
];

const BANDS: SupportNeedBand[] = ["minimal", "mild", "moderate", "substantial"];

const BAND_COLORS: Record<SupportNeedBand, string> = {
  minimal: "green",
  mild: "gold",
  moderate: "orange",
  substantial: "red",
};

const columns: ColumnsType<AssessmentListItem> = [
  { title: "Assessment", dataIndex: "assessment_id" },
  {
    title: "Assessed At",
    dataIndex: "assessed_at",
    render: (value: string) => new Date(value).toLocaleDateString(),
  },
  { title: "Clinician", dataIndex: "clinician_id" },
  {
    title: "Flagged",
    dataIndex: "flagged",
    render: (value: boolean) => (value ? <Tag color="red">Flagged</Tag> : <Tag>No</Tag>),
  },
  {
    title: "Domains",
    dataIndex: "domains",
    render: (domains: DomainResult[]) => (
      <>
        {domains.map((result) =>
          result.band ? (
            <Tag color={BAND_COLORS[result.band]} key={result.domain}>
              {result.domain}: {result.band}
            </Tag>
          ) : null,
        )}
      </>
    ),
  },
];

interface AssessmentQueueProps {
  onSelect?: (assessmentId: string) => void;
}

const AssessmentQueue: FunctionComponent<AssessmentQueueProps> = ({ onSelect }) => {
  const [clinicianId, setClinicianId] = useState<string | undefined>(undefined);
  const [flagged, setFlagged] = useState<boolean | undefined>(undefined);
  const [domain, setDomain] = useState<DomainName | undefined>(undefined);
  const [band, setBand] = useState<SupportNeedBand | undefined>(undefined);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [selectedId, setSelectedId] = useState<string | undefined>(undefined);

  const [items, setItems] = useState<AssessmentListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    listAssessments({
      status: "pending_review",
      clinician_id: clinicianId,
      flagged,
      domain,
      band,
      page,
      page_size: pageSize,
      sort_by: "assessed_at",
      sort_order: "desc",
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
  }, [clinicianId, flagged, domain, band, page, pageSize]);

  const handleTableChange = (pagination: TablePaginationConfig) => {
    setPage(pagination.current ?? 1);
    setPageSize(pagination.pageSize ?? 10);
  };

  return (
    <Card title="Assessment Queue">
      <Row gutter={8} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Input
            allowClear
            placeholder="Clinician"
            value={clinicianId}
            onChange={(event) => {
              setPage(1);
              setClinicianId(event.target.value || undefined);
            }}
          />
        </Col>
        <Col span={6}>
          <Select
            allowClear
            placeholder="Flagged"
            style={{ width: "100%" }}
            value={flagged}
            onChange={(value) => {
              setPage(1);
              setFlagged(value);
            }}
            options={[
              { label: "Flagged", value: true },
              { label: "Not flagged", value: false },
            ]}
          />
        </Col>
        <Col span={6}>
          <Select
            allowClear
            placeholder="Domain"
            style={{ width: "100%" }}
            value={domain}
            onChange={(value) => {
              setPage(1);
              setDomain(value);
            }}
            options={DOMAINS.map((value) => ({ label: value, value }))}
          />
        </Col>
        <Col span={6}>
          <Select
            allowClear
            placeholder="Band"
            style={{ width: "100%" }}
            value={band}
            onChange={(value) => {
              setPage(1);
              setBand(value);
            }}
            options={BANDS.map((value) => ({ label: value, value }))}
          />
        </Col>
      </Row>
      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}
      <Table<AssessmentListItem>
        rowKey="assessment_id"
        columns={columns}
        dataSource={items}
        loading={loading}
        pagination={{ current: page, pageSize, total, showSizeChanger: true }}
        onChange={handleTableChange}
        onRow={(record) => ({
          onClick: () => {
            setSelectedId(record.assessment_id);
            onSelect?.(record.assessment_id);
          },
        })}
        rowClassName={(record) => (record.assessment_id === selectedId ? "ant-table-row-selected" : "")}
      />
    </Card>
  );
};

export default AssessmentQueue;
