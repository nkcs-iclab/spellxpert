import csc.datasets.utils
import csc.datasets.base

from csc.datasets.stcn import STCNDataset
from csc.datasets.cscd_ns import CSCDNSDataset
from csc.datasets.cscd_ns_reasoning import CSCDNSReasoningDataset

datasets = {
    'stcn': STCNDataset,
    'stcn-reasoning': STCNDataset,
    'cscd-ns': CSCDNSDataset,
    'cscd-ns-reasoning': CSCDNSReasoningDataset,
}
