import argparse
import logging
import sys

from candidate_models import score_model, Defaults
from candidate_models.models import models, infer_image_size
from candidate_models.models.implementations import Defaults as DeepModelDefaults
from candidate_models.models.implementations import model_layers

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, required=True, choices=models.keys())
    parser.add_argument('--model_weights', type=str, default=DeepModelDefaults.weights)
    parser.add_argument('--layers', type=str, nargs='+', default=None)
    parser.add_argument('--pca', type=int, default=DeepModelDefaults.pca_components,
                        help='Number of components to reduce the flattened features to')
    parser.add_argument('--no-pca', action='store_const', const=None, dest='pca')
    parser.add_argument('--benchmark', type=str, default=Defaults.benchmark)
    parser.add_argument('--image_size', type=int, default='from_model')
    parser.add_argument('--log_level', type=str, default='INFO')
    args = parser.parse_args()
    print(args.model)
    if args.image_size == 'from_model':
        args.image_size = infer_image_size(args.model)
    args.layers = args.layers or model_layers[args.model]
    logging.basicConfig(stream=sys.stdout, level=logging.getLevelName(args.log_level))
    logging.getLogger("peewee").setLevel(logging.WARNING)
    logger.info("Running with args %s", vars(args))

    logger.info('Scoring model')
    score = score_model(args.model, layers=args.layers, weights=args.model_weights,
                        pca_components=args.pca, image_size=args.image_size,
                        benchmark=args.benchmark)
    if args.benchmark == 'brain-score':
        score = score.values.sel(benchmark='dicarlo.Majaj2015')
        for region in score['region'].values:
            print(region)
            region_score = score.sel(region=region)
            best_value = region_score.sel(aggregation='center').values == \
                         region_score.sel(aggregation='center').values.max()
            print("\n".join([f"{layer}: {center:.3f}+-{error:.3f} {best}" for layer, center, error, best in zip(
                region_score['layer'].values.tolist(),
                region_score.sel(aggregation='center').values.tolist(),
                region_score.sel(aggregation='error').values.tolist(),
                [["", "[best]"][is_best] for is_best in best_value])]))
            print()


main()
