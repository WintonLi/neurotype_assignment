import type { FunctionComponent } from "react";
import AssessmentTable from "./AssessmentTable";

interface IssuedAssessmentProps {
  onSelect?: (assessmentId: string | undefined) => void;
  refreshToken?: number;
}

const IssuedAssessment: FunctionComponent<IssuedAssessmentProps> = ({ onSelect, refreshToken }) => (
  <AssessmentTable
    status="issued"
    title="Issued Assessments"
    onSelect={onSelect}
    refreshToken={refreshToken}
  />
);

export default IssuedAssessment;