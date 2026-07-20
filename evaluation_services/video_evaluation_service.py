#NEW CODE BELOW 
"""Service that handles video evaluations using AI (LLMs and/or annotations)."""

import functools
import logging

import configuration
import models
from custom_evaluation import custom_detector
from features_repository import feature_configs_handler
from gcp_api_services import gcs_api_service
from helpers import generic_helpers
from llms_evaluation import llms_detector


class VideoEvaluationService:
  """Service that evaluates configured video features."""

  def evaluate_features(
      self,
      config: configuration.Configuration,
      video_uri: str,
      features_category: models.VideoFeatureCategory,
  ) -> list[models.FeatureEvaluation]:
    """Run evaluation for the requested Long Form ABCD or Shorts category."""

    if config.extract_brand_metadata:
      metadata = llms_detector.llms_detector.get_video_metadata(config, video_uri)
      config.brand_name = metadata.get("brand_name")
      config.brand_variations = metadata.get("brand_variations")
      config.branded_products = metadata.get("branded_products")
      config.branded_products_categories = metadata.get(
          "branded_products_categories"
      )
      config.branded_call_to_actions = metadata.get(
          "branded_call_to_actions"
      )

    feature_evaluations: list[models.FeatureEvaluation] = []
    tasks = []

    feature_groups = (
        feature_configs_handler.features_configs_handler
        .get_features_by_category_by_group_config(features_category)
    )

    # Build the lookup only from the category currently being evaluated.
    # Long Form and the custom Shorts repository reuse IDs, so a global
    # get_feature_by_id() lookup can attach a Long Form definition to a Shorts
    # result and lose Shorts-only metadata such as include_in_evaluation=False.
    feature_lookup: dict[str, models.VideoFeature] = {
        feature.id: feature
        for grouped_features in feature_groups.values()
        for feature in grouped_features
    }

    for group_key, feature_configs in feature_groups.items():
      if config.use_llms and not config.use_annotations:
        (
            feature_configs_handler.features_configs_handler
            .change_evaluation_method_to_llms_only(feature_configs)
        )

      if (
          group_key == models.VideoSegment.NONE.value
          and config.use_annotations
          and config.creative_provider_type == models.CreativeProviderType.GCS
      ):
        # NO_GROUPING features are executed separately.
        for feature_config in feature_configs:
          if (
              feature_config.video_segment
              == models.VideoSegment.FIRST_5_SECS_VIDEO
          ):
            evaluation_uri = (
                gcs_api_service.gcs_api_service.get_reduced_uri(
                    config, video_uri
                )
            )
          else:
            evaluation_uri = video_uri

          if self.is_custom_evaluation(feature_config.evaluation_function):
            task = functools.partial(
                custom_detector.custom_detector.evaluate_features,
                config,
                feature_config,
                evaluation_uri,
            )
          else:
            task = functools.partial(
                llms_detector.llms_detector.evaluate_features,
                config,
                {
                    "category": features_category,
                    "group_by": f"{group_key}-{feature_config.id}",
                    "video_uri": evaluation_uri,
                    # Send only this feature so an ungrouped request remains
                    # independent from the other feature results.
                    "feature_configs": [feature_config],
                },
            )
          tasks.append(task)
      else:
        if (
            group_key == models.VideoSegment.FIRST_5_SECS_VIDEO.value
            and config.creative_provider_type == models.CreativeProviderType.GCS
        ):
          evaluation_uri = (
              gcs_api_service.gcs_api_service.get_reduced_uri(config, video_uri)
          )
        else:
          evaluation_uri = video_uri

        task = functools.partial(
            llms_detector.llms_detector.evaluate_features,
            config,
            {
                "category": features_category,
                "group_by": f"{group_key} for video {evaluation_uri}",
                "video_uri": evaluation_uri,
                "feature_configs": feature_configs,
            },
        )
        tasks.append(task)

    logging.info(
        "Starting evaluation for %s: %d configured features in %d task(s).",
        features_category.value,
        len(feature_lookup),
        len(tasks),
    )

    detector_results = generic_helpers.execute_tasks_in_parallel(tasks)

    for result_group in detector_results:
      if not result_group:
        continue

      for evaluated_feature in result_group:
        feature_id = evaluated_feature.get("id")
        feature = feature_lookup.get(feature_id)

        if feature is None:
          logging.warning(
              "Feature %s was not found in selected category %s and was skipped.",
              feature_id,
              features_category.value,
          )
          continue

        feature_evaluations.append(
            models.FeatureEvaluation(
                feature=feature,
                detected=bool(evaluated_feature.get("detected")),
                confidence_score=evaluated_feature.get("confidence_score"),
                rationale=evaluated_feature.get("rationale") or "",
                evidence=evaluated_feature.get("evidence") or "",
                strengths=evaluated_feature.get("strengths") or "",
                weaknesses=evaluated_feature.get("weaknesses") or "",
            )
        )

    feature_evaluations.sort(
        key=lambda feature_eval: (
            feature_eval.feature.sub_category.value,
            feature_eval.feature.id,
        )
    )

    scoreable_count = sum(
        1
        for feature_eval in feature_evaluations
        if getattr(feature_eval.feature, "include_in_evaluation", True)
    )
    logging.info(
        "Completed %s evaluation: %d returned, %d included in scoring, %d excluded.",
        features_category.value,
        len(feature_evaluations),
        scoreable_count,
        len(feature_evaluations) - scoreable_count,
    )

    return feature_evaluations

  def is_custom_evaluation(self, function_name: str | None) -> bool:
    """Return True when a custom annotation function is configured."""
    return bool(function_name)


video_evaluation_service = VideoEvaluationService()

#NEW CODE ABOVE 

#OLD CODE BELOW 
# """Service that handles video evaluations using AI (LLMs and/or Annotations)"""

# import logging
# import functools
# import models
# import configuration
# from features_repository import feature_configs_handler
# from llms_evaluation import llms_detector
# from custom_evaluation import custom_detector
# from helpers import generic_helpers
# from gcp_api_services import gcs_api_service


# class VideoEvaluationService:
#   """Service that handles video evaluations using AI (LLMs and/or Annotations)"""

#   def __init__(self):
#     pass

#   def evaluate_features(
#       self,
#       config: configuration.Configuration,
#       video_uri: str,
#       features_category: models.VideoFeatureCategory,
#   ):
#     """Run ABCD evaluation on videos for Full ABCD features or Shorts"""

#     if config.extract_brand_metadata:
#       metadata = llms_detector.llms_detector.get_video_metadata(
#           config, video_uri
#       )
#       config.brand_name = metadata.get("brand_name")
#       config.brand_variations = metadata.get("brand_variations")
#       config.branded_products = metadata.get("branded_products")
#       config.branded_products_categories = metadata.get(
#           "branded_products_categories"
#       )
#       config.branded_call_to_actions = metadata.get("branded_call_to_actions")

#     feature_evaluations: list[models.FeatureEvaluation] = []
#     tasks = []
#     feature_groups = feature_configs_handler.features_configs_handler.get_features_by_category_by_group_config(
#         features_category
#     )
#     uri = video_uri  # use full video uri by default

#     for group_key in feature_groups:
#       feature_configs: list[models.VideoFeature] = feature_groups.get(group_key)

#       # Use LLM evaluation method only
#       if config.use_llms and not config.use_annotations:
#         feature_configs_handler.features_configs_handler.change_evaluation_method_to_llms_only(
#             feature_configs
#         )

#       # Process the features that are not grouped individually
#       # meaning, each will be a separate request to the LLM
#       if (
#           group_key == "NO_GROUPING"
#           and config.use_annotations
#           and config.creative_provider_type == models.CreativeProviderType.GCS
#           # For now only GCS creative providers using annotations can be processed individually
#       ):
#         for f_config in feature_configs:
#           if (
#               f_config.video_segment.value
#               == models.VideoSegment.FIRST_5_SECS_VIDEO.value
#           ):
#             uri = gcs_api_service.gcs_api_service.get_reduced_uri(
#                 config, video_uri
#             )
#           else:
#             uri = video_uri

#           # Build function to execute in parallel
#           # If custom detector was not defined, default to LLMs
#           if self.is_custom_evaluation(f_config.evaluation_function):
#             func = functools.partial(
#                 custom_detector.custom_detector.evaluate_features,
#                 config,
#                 f_config,
#                 uri,
#             )
#           else:
#             func = functools.partial(
#                 llms_detector.llms_detector.evaluate_features,
#                 config,
#                 {
#                     "category": features_category,
#                     "group_by": f"{group_key}-{f_config.id}",
#                     "video_uri": uri,
#                     "feature_configs": (
#                         feature_configs
#                     ),  # process feature individually
#                 },
#             )
#           # Add task to be process
#           tasks.append(func)
#       else:
#         # Use full video for Public URL videos
#         if (
#             group_key == models.VideoSegment.FIRST_5_SECS_VIDEO.value
#             and config.creative_provider_type == models.CreativeProviderType.GCS
#         ):
#           uri = gcs_api_service.gcs_api_service.get_reduced_uri(
#               config, video_uri
#           )
#         else:
#           uri = video_uri

#         # Build function to execute in parallel
#         func = functools.partial(
#             llms_detector.llms_detector.evaluate_features,
#             config,
#             {
#                 "category": features_category,
#                 "group_by": f"{group_key} for video {uri}",
#                 "video_uri": uri,
#                 "feature_configs": (
#                     feature_configs
#                 ),  # process feature individually
#             },
#         )
#         # Add task to be process
#         tasks.append(func)

#     logging.info("Starting ABCD evaluation for features... \n")

#     llm_evals = generic_helpers.execute_tasks_in_parallel(tasks)

#     # Process LLM results and create feature objs in the required format
#     for evals in llm_evals:
#       for evaluated_feature in evals:
#         feature: models.VideoFeature = (
#             feature_configs_handler.features_configs_handler.get_feature_by_id(
#                 evaluated_feature.get("id")
#             )
#         )
#         if feature:
#           feature_evaluations.append(
#               models.FeatureEvaluation(
#                   feature=feature,
#                   detected=evaluated_feature.get("detected"),
#                   confidence_score=evaluated_feature.get("confidence_score"),
#                   rationale=evaluated_feature.get("rationale"),
#                   evidence=evaluated_feature.get("evidence"),
#                   strengths=evaluated_feature.get("strengths"),
#                   weaknesses=evaluated_feature.get("weaknesses"),
#               )
#           )
#         else:
#           logging.warning(
#               "Feature %s not found. Feature was not added to"
#               " feature_evaluations.",
#               evaluated_feature.get("id"),
#           )

#     # Sort features by category and id for presentation
#     if features_category == models.VideoFeatureCategory.LONG_FORM_ABCD:
#       feature_evaluations = sorted(
#           feature_evaluations,
#           key=lambda feature_eval: (
#               feature_eval.feature.category.value,
#               feature_eval.feature.id,
#           ),
#           reverse=False,
#       )

#     return feature_evaluations

#   def is_custom_evaluation(self, function_name):
#     return function_name != ""


# video_evaluation_service = VideoEvaluationService()
