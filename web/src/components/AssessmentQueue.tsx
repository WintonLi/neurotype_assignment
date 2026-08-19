import type { FunctionComponent } from "react";
import AssessmentTable from "./AssessmentTable";

interface AssessmentQueueProps {
  onSelect?: (assessmentId: string | undefined) => void;
  refreshToken?: number;
}

const AssessmentQueue: FunctionComponent<AssessmentQueueProps> = ({ onSelect, refreshToken }) => (
  <AssessmentTable
    status="pending_review"
    title="Assessment Queue"
    onSelect={onSelect}
    refreshToken={refreshToken}
  />
);

export default AssessmentQueue;
