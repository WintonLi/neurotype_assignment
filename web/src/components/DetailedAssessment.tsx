import type { FunctionComponent } from "react";
import { useEffect, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Empty,
  Input,
  Popconfirm,
  Space,
  Spin,
  Tag,
  Typography,
  message,
  notification,
} from "antd";
import type {
  AssessmentDetail,
  DomainResult,
  SupportNeedBand,
} from "../services/assessmentService";
import { getAssessment, issueAssessment, updateAssessmentSummary } from "../services/assessmentService";

const { Text, Paragraph } = Typography;
const { TextArea } = Input;

const BAND_COLORS: Record<SupportNeedBand, string> = {
  minimal: "green",
  mild: "gold",
  moderate: "orange",
  substantial: "red",
};

const renderDomain = (domain: DomainResult) => (
  <div key={domain.domain} style={{ marginBottom: 8 }}>
    <Space>
      <Text strong>{domain.domain}</Text>
      {domain.band && <Tag color={BAND_COLORS[domain.band]}>{domain.band}</Tag>}
      <Text type="secondary">
        {domain.percentage === null ? "no score" : `${domain.percentage.toFixed(1)}%`}
      </Text>
    </Space>
    <div>
      {domain.items.map((item) => (
        <Tag key={item.code} color={item.completed ? undefined : "default"}>
          {item.code}: {item.completed ? `${item.raw}/${item.max}` : "incomplete"}
        </Tag>
      ))}
    </div>
  </div>
);

interface DetailedAssessmentProps {
  assessmentId?: string;
  onChanged?: () => void;
  showIssueButton?: boolean;
}

const DetailedAssessment: FunctionComponent<DetailedAssessmentProps> = ({
  assessmentId,
  onChanged,
  showIssueButton = true,
}) => {
  const [detail, setDetail] = useState<AssessmentDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [issuing, setIssuing] = useState(false);
  const [editingSummary, setEditingSummary] = useState(false);
  const [summaryDraft, setSummaryDraft] = useState("");
  const [savingSummary, setSavingSummary] = useState(false);

  useEffect(() => {
    if (!assessmentId) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    setEditingSummary(false);
    getAssessment(assessmentId)
      .then((response) => {
        if (cancelled) return;
        setDetail(response);
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
  }, [assessmentId]);

  const handleIssue = async () => {
    if (!assessmentId) return;
    setIssuing(true);
    try {
      await issueAssessment(assessmentId);
      message.success("Assessment issued");
      const refreshed = await getAssessment(assessmentId);
      setDetail(refreshed);
      onChanged?.();
    } catch (err) {
      notification.error({
        message: "Failed to issue assessment",
        description: (err as Error).message,
        closable: true,
      });
    } finally {
      setIssuing(false);
    }
  };

  const startEditingSummary = () => {
    if (!detail) return;
    setSummaryDraft(detail.summary);
    setEditingSummary(true);
  };

  const handleSaveSummary = async () => {
    if (!assessmentId) return;
    setSavingSummary(true);
    try {
      const response = await updateAssessmentSummary(assessmentId, summaryDraft);
      setDetail((current) =>
        current && { ...current, summary: response.summary, flagged: response.flagged },
      );
      setEditingSummary(false);
      message.success("Summary updated");
      onChanged?.();
    } catch (err) {
      notification.error({
        message: "Failed to update summary",
        description: (err as Error).message,
        closable: true,
      });
    } finally {
      setSavingSummary(false);
    }
  };

  if (!assessmentId) {
    return (
      <Card title="Assessment Detail">
        <Empty description="Select an assessment from the queue" />
      </Card>
    );
  }

  return (
    <Card
      title={detail ? detail.assessment_id : "Assessment Detail"}
      extra={
        detail && (
          <Space>
            {showIssueButton && (
              <Popconfirm
                title="Issue this report?"
                description="Issuing cannot be undone."
                onConfirm={handleIssue}
                disabled={detail.status === "issued"}
              >
                <Button type="primary" loading={issuing} disabled={detail.status === "issued"}>
                  {detail.status === "issued" ? "Issued" : "Issue"}
                </Button>
              </Popconfirm>
            )}
            <Button onClick={startEditingSummary} disabled={editingSummary}>
              Edit Summary
            </Button>
          </Space>
        )
      }
    >
      {loading && <Spin />}
      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}
      {detail && !loading && (
        <>
          <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
            <Descriptions.Item label="Status">
              <Tag color={detail.status === "issued" ? "green" : "blue"}>{detail.status}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Flagged">
              {detail.flagged ? <Tag color="red">Flagged</Tag> : <Tag>No</Tag>}
            </Descriptions.Item>
            <Descriptions.Item label="Clinician">{detail.clinician_id}</Descriptions.Item>
            <Descriptions.Item label="Assessed At">
              {new Date(detail.assessed_at).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="Age">
              {detail.age.years}y {detail.age.months}m
            </Descriptions.Item>
            <Descriptions.Item label="Date of Birth">{detail.client.date_of_birth}</Descriptions.Item>
            <Descriptions.Item label="NHS Number">{detail.client.nhs_number}</Descriptions.Item>
            <Descriptions.Item label="Guardian Contact">
              {detail.client.guardian_contact}
            </Descriptions.Item>
            <Descriptions.Item label="Safeguarding Notes" span={2}>
              {detail.client.safeguarding_notes ?? "-"}
            </Descriptions.Item>
            {detail.status === "issued" && (
              <>
                <Descriptions.Item label="Issued At">
                  {detail.issued_at && new Date(detail.issued_at).toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="Issued By">{detail.issued_by}</Descriptions.Item>
              </>
            )}
          </Descriptions>

          {detail.domains.map(renderDomain)}

          <Typography.Title level={5} style={{ marginTop: 16 }}>
            Summary
          </Typography.Title>
          {editingSummary ? (
            <Space direction="vertical" style={{ width: "100%" }}>
              <TextArea
                value={summaryDraft}
                onChange={(event) => setSummaryDraft(event.target.value)}
                rows={6}
                maxLength={8000}
              />
              <Space>
                <Button type="primary" loading={savingSummary} onClick={handleSaveSummary}>
                  Save
                </Button>
                <Button onClick={() => setEditingSummary(false)} disabled={savingSummary}>
                  Cancel
                </Button>
              </Space>
            </Space>
          ) : (
            <Paragraph>{detail.summary}</Paragraph>
          )}
        </>
      )}
    </Card>
  );
};

export default DetailedAssessment;

