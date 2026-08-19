import type { FunctionComponent } from 'react';
import { useState } from 'react';
import { Row, Col } from 'antd';
import DetailedAssessment from '../components/DetailedAssessment';
import IssuedAssessment from '../components/IssusedAssessment';
interface IssuedProps {
    
}

const Issued: FunctionComponent<IssuedProps> = () => {
  const [selectedAssessmentId, setSelectedAssessmentId] = useState<string | undefined>(undefined);
  const [refreshToken, setRefreshToken] = useState(0);

  return (
    <Row>
      <Col span={12}>
        <IssuedAssessment onSelect={setSelectedAssessmentId} refreshToken={refreshToken} />
      </Col>

      <Col span={12}>
        <DetailedAssessment
          assessmentId={selectedAssessmentId}
          showIssueButton={false}
          onChanged={() => setRefreshToken((token) => token + 1)}
        />
      </Col>
    </Row>
  );
}

export default Issued;