from csc.data.datasets.cscd_ns import CSCDNSDataset
from csc.data.datasets.lemon_v2 import LemonV2Dataset
from csc.data.datasets.stcn import STCNDataset

datasets = {
    'cscd-ns': CSCDNSDataset,
    'lemon-v2': LemonV2Dataset,
    'stcn': STCNDataset,
    'tianjindaily': STCNDataset,
}
