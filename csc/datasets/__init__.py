import csc.datasets.template
import csc.datasets.utils
import csc.datasets.detection

from csc.datasets.cscd_ns.detection import CSCDNSDetectionDataset
from csc.datasets.stcn.detection import STCNDetectionDataset

datasets = {
    'cscd-ns.detection': CSCDNSDetectionDataset,
    'stcn-g1.detection': STCNDetectionDataset,
    'stcn-g2.detection': STCNDetectionDataset,
}
