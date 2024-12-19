import csc.datasets.template
import csc.datasets.utils
import csc.datasets.detection

from csc.datasets.stcn.detection import STCNDetectionDataset
from csc.datasets.cscd_ns.detection import CSCDNSDetectionDataset

datasets = {
    'stcn-g1.detection': STCNDetectionDataset,
    'stcn-g2.detection': STCNDetectionDataset,
    'cscd-ns.detection': CSCDNSDetectionDataset,
}
