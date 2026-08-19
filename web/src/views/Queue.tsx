import type { FunctionComponent } from "react";
import { useState } from "react";
import { Row, Col } from "antd";
import AssessmentQueue from "../components/AssessmentQueue";
import DetailedAssessment from "../components/DetailedAssessment";

interface QueueProps {}

const Queue: FunctionComponent<QueueProps> = () => {
  const [selectedAssessmentId, setSelectedAssessmentId] = useState<string | undefined>(undefined);
  const [refreshToken, setRefreshToken] = useState(0);

  return (
    <Row>
      <Col span={12}>
        <AssessmentQueue onSelect={setSelectedAssessmentId} refreshToken={refreshToken} />
      </Col>

      <Col span={12}>
        <DetailedAssessment
          assessmentId={selectedAssessmentId}
          onChanged={() => setRefreshToken((token) => token + 1)}
        />
      </Col>
    </Row>
  );
};

export default Queue;

