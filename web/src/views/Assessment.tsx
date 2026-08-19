import type { FunctionComponent } from 'react';
import { Row, Col } from 'antd';
import DetailedAssessment from '../components/DetailedAssessment';
import IssuedAssessment from '../components/IssusedAssessment';
interface IssuedProps {
    
}

const Issued: FunctionComponent<IssuedProps> = () => {
//   const detailedAssessment = useAssessmentStore(state => state.detailedAssessment);

  return (
    <Row>
      <Col span={12}>
        <IssuedAssessment />
      </Col>

      <Col span={12}>
        <DetailedAssessment />
      </Col>
    </Row>
  );
}

export default Issued;