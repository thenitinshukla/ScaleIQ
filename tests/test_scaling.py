"""
Unit tests for scaling engine.
"""

import unittest
from core.config import ScalingConfig, ResourceConfig
from core.types import ScalingType
from engine.scaling import ScalingEngine


class TestScalingEngine(unittest.TestCase):
    """Test cases for scaling configuration generator."""
    
    def setUp(self):
        """Setup test fixtures."""
        self.resource_config = ResourceConfig(
            max_nodes=64,
            procs_per_node=128
        )
    
    def test_strong_scaling_generation(self):
        """Test strong scaling configuration generation."""
        scaling_config = ScalingConfig(
            scaling_type=ScalingType.STRONG,
            max_nodes=8,
            initial_procs=(2, 2, 2),
            initial_domain=(10.0, 10.0, 10.0),
            initial_cells=(256, 256, 256)
        )
        
        engine = ScalingEngine(scaling_config, self.resource_config)
        configs = engine.generate_job_configs()
        
        # Should generate configs for 1, 2, 4, 8 nodes
        self.assertEqual(len(configs), 4)
        
        # Check first config
        self.assertEqual(configs[0].num_nodes, 1)
        self.assertEqual(configs[0].num_procs, 128)
        
        # Check last config
        self.assertEqual(configs[-1].num_nodes, 8)
        self.assertEqual(configs[-1].num_procs, 1024)
        
        # Domain should remain constant for strong scaling
        for config in configs:
            self.assertEqual(config.domain_size, (10.0, 10.0, 10.0))
            self.assertEqual(config.cell_count, (256, 256, 256))
    
    def test_weak_scaling_generation(self):
        """Test weak scaling configuration generation."""
        scaling_config = ScalingConfig(
            scaling_type=ScalingType.WEAK,
            max_nodes=4,
            initial_procs=(2, 2, 2),
            initial_domain=(10.0, 10.0, 10.0),
            initial_cells=(256, 256, 256)
        )
        
        engine = ScalingEngine(scaling_config, self.resource_config)
        configs = engine.generate_job_configs()
        
        # Should generate configs for 1, 2, 4 nodes
        self.assertEqual(len(configs), 3)
        
        # Problem size should scale with node count
        self.assertIsNotNone(configs[0].domain_size)
        self.assertIsNotNone(configs[-1].domain_size)
        
        # Domain should grow for weak scaling
        self.assertGreater(configs[-1].domain_size[0], configs[0].domain_size[0])
    
    def test_node_sequence_generation(self):
        """Test custom node sequence."""
        scaling_config = ScalingConfig(
            scaling_type=ScalingType.STRONG,
            max_nodes=10,
            node_sequence=[1, 3, 5, 7, 10]
        )
        
        engine = ScalingEngine(scaling_config, self.resource_config)
        configs = engine.generate_job_configs()
        
        # Should use custom sequence
        self.assertEqual(len(configs), 5)
        self.assertEqual([c.num_nodes for c in configs], [1, 3, 5, 7, 10])
    
    def test_power_of_two_sequence(self):
        """Test default power-of-2 node sequence."""
        scaling_config = ScalingConfig(
            scaling_type=ScalingType.STRONG,
            max_nodes=16
        )
        
        sequence = scaling_config.get_node_sequence()
        
        # Should generate: 1, 2, 4, 8, 16
        self.assertEqual(sequence, [1, 2, 4, 8, 16])


if __name__ == '__main__':
    unittest.main()
