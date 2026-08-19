import type { FunctionComponent } from "react";
import { Row, Col } from "antd";
import AssessmentQueue from "../components/AssessmentQueue";
import DetailedAssessment from "../components/DetailedAssessment";

interface QueueProps {}

const Queue: FunctionComponent<QueueProps> = () => {
  return (
    <Row>
      <Col span={16}>
        <AssessmentQueue />
      </Col>

      <Col span={8}>
        <DetailedAssessment />
      </Col>
    </Row>
  );
};

export default Queue;
