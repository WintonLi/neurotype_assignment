import type { FunctionComponent } from 'react';
import { Row, Col } from 'antd';
import AssessmentQueue from '../components/AssessmentQueue';
import DetailedAssessment from '../components/DetailedAssessment';
interface AssessmentProps {
    
}

const Assessment: FunctionComponent<AssessmentProps> = () => {
//   const detailedAssessment = useAssessmentStore(state => state.detailedAssessment);

  return (
    <Row>
      <Col span={12}>
        <AssessmentQueue />
      </Col>

      <Col span={12}>
        <DetailedAssessment />
      </Col>
    </Row>
  );
}

export default Assessment;