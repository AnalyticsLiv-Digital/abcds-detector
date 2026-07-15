#!/usr/bin/env python3

###########################################################################
#
#  Copyright 2024 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
###########################################################################

"""Module with the supported ABCD feature configurations for Full ABCDs.

ABCD 2.0 upgrade:
- Keeps the same repository structure, feature IDs, evaluation methods, and return function.
- Adds funnel-aware creative reasoning without requiring a new API/input field.
- Moves prompts from pure binary compliance to performance-aware quality judgment.
- Adds prominence scoring, clutter/cognitive-load checks, near-miss handling, and richer logs.
"""

from models import (
    VideoFeature,
    VideoFeatureCategory,
    VideoSegment,
    EvaluationMethod,
    VideoFeatureSubCategory, 
)


FUNNEL_AWARE_EVALUATION_INSTRUCTIONS = """
Before evaluating this feature, infer the likely funnel intent of the ad creative using only
video content, speech, text overlays, visual hierarchy, CTA strength, brand/product presence,
urgency, offer language, problem-solution structure, and available metadata. Do not assume the
advertiser's real campaign objective.

Classify the likely creative intent as:
- TOFU / Awareness: mainly attracts attention, builds brand recall, creates broad emotional memory,
  or introduces the brand/product.
- MOFU / Consideration: mainly explains benefits, solves a problem, builds trust, compares options,
  or helps viewers evaluate the product/service.
- BOFU / Conversion: mainly pushes immediate action such as call, try, buy, sign up, download,
  book, claim an offer, start a trial, or convert now.

Always include in the reasoning:
- Inferred Funnel Intent: TOFU, MOFU, or BOFU
- Reason for the inferred funnel intent
- Whether this feature is strong or weak for that inferred funnel intent
"""

PROMINENCE_QUALITY_SCALE_INSTRUCTIONS = """
Rate the feature quality/prominence from 1 to 5:
1 = Technical presence only; weak, hidden, confusing, or low impact.
2 = Present but secondary, small, low contrast, vague, or easy to miss.
3 = Clear and acceptable; understandable and reasonably visible/audible.
4 = Strong; prominent, clear, persuasive, and well-integrated.
5 = Hero-level execution; highly memorable, market-ready, and clearly drives the intended response.
Include the score as: Prominence/Quality Score: #/5.
"""

CLUTTER_PENALTY_INSTRUCTIONS = """
Check for cognitive load or clutter. If logo, product, partner brand, CTA, subtitles, offers,
and multiple text lines compete in the same frame, mention that this weakens effectiveness.
Do not reward an ad only because it technically contains many elements.
"""

NEAR_MISS_INSTRUCTIONS = """
Apply the Near-Miss Rule for timing-sensitive criteria. Small deviations from a timing threshold
should be recognized in the reasoning instead of being treated as total creative failure. If the
creative intent is strong but slightly late/early, mention it as a near miss and explain whether
human impact is still acceptable.
"""

EVIDENCE_INSTRUCTIONS = """
Provide exact timestamps and concrete visual/audio evidence. Do not guess. If evidence is weak
or ambiguous, say so clearly.
"""


# Common instruction bundles. Keeping these small avoids changing the data model.
GENERAL_CREATIVE_INSTRUCTIONS = [
    FUNNEL_AWARE_EVALUATION_INSTRUCTIONS,
    PROMINENCE_QUALITY_SCALE_INSTRUCTIONS,
    CLUTTER_PENALTY_INSTRUCTIONS,
    EVIDENCE_INSTRUCTIONS,
]

TIMING_CREATIVE_INSTRUCTIONS = [
    FUNNEL_AWARE_EVALUATION_INSTRUCTIONS,
    NEAR_MISS_INSTRUCTIONS,
    PROMINENCE_QUALITY_SCALE_INSTRUCTIONS,
    CLUTTER_PENALTY_INSTRUCTIONS,
    EVIDENCE_INSTRUCTIONS,
]



def get_long_form_abcd_feature_configs() -> list[VideoFeature]:
  """Gets all the supported ABCD features.

  Returns:
    feature_configs: list of feature configurations
  """
  feature_configs = [
      VideoFeature(
          id="a_dynamic_start",
          name="Dynamic Start",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.ATTRACT,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                The opening should create immediate viewer attention through a meaningful visual hook,
                scene change, focal shift, emotional contrast, or strong creative movement early in the video.
                The ideal first major hook or shot change occurs between 1.0 and 2.0 seconds, but near-misses
                should be judged based on likely human attention impact rather than rigid binary timing alone.
            """,
          prompt_template="""
                Evaluate whether the video has a dynamic and attention-worthy start.

                Do not only check whether the first shot changes mechanically between 1.0 and 2.0 seconds.
                Also evaluate whether the opening creates a strong human attention hook through visual contrast,
                motion, emotion, focal point shift, surprising text, or a clear problem setup.

                Return True if the opening has a strong attention hook or meaningful shot/focal change early enough
                to likely keep the viewer engaged. Return False if the opening is static, slow, unclear, or lacks
                stop-power.
            """,
          extra_instructions=TIMING_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide the exact timestamp when the first major hook, shot change, or focal shift occurs.",
              "Explain whether the opening has stop-power for the inferred funnel intent.",
              "Return True only if the dynamic-start quality score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.ANNOTATIONS,
          evaluation_function="detect_dynamic_start",
          include_in_evaluation=True,
          group_by=VideoSegment.NONE,
      ),
      VideoFeature(
          id="a_quick_pacing",
          name="Quick Pacing",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.ATTRACT,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                The video should maintain viewer attention through meaningful pacing, visual variety,
                and focal point progression. Fast cutting alone is not enough; pacing should help the
                message become more engaging and easier to follow.
            """,
          prompt_template="""
                Does the video use effective pacing to maintain viewer attention across the full video?

                Count meaningful scene changes, focal point shifts, background/location changes, and visual
                progressions. Ignore meaningless movement that does not improve attention or comprehension.
                Fast pacing should not create clutter or confusion.

                Return True if the pacing is engaging, varied, and appropriate for the inferred funnel intent.
                Return False if the video feels slow, repetitive, visually flat, or confusing due to excessive cuts.
            """,
          extra_instructions=GENERAL_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide the meaningful change count in the following format: Number of meaningful changes: #",
              "Provide exact timestamps for meaningful shot changes and briefly describe each change.",
              "Explain whether the pacing helps attention or creates cognitive overload.",
              "Return True only if pacing quality score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.ANNOTATIONS,
          evaluation_function="detect_quick_pacing",
          include_in_evaluation=True,
          group_by=VideoSegment.NONE,
      ),
      VideoFeature(
          id="a_quick_pacing_1st_5_secs",
          name="Quick Pacing (First 5 seconds)",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.ATTRACT,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                The first 5 seconds should contain at least one meaningful visual change, cut,
                camera movement, focal point shift, text reveal, or creative transition that helps hold
                attention. The change should support viewer engagement, not just satisfy motion.
            """,
          prompt_template="""
                Are the first 5 seconds visually engaging through at least one meaningful shot change,
                visual cut, camera change, text reveal, focal point shift, or creative transition?

                Do not reward meaningless motion. Evaluate whether the early pacing creates actual stop-power
                and supports the inferred funnel intent.

                Return True if the first 5 seconds contain meaningful visual progression. Return False if
                the opening remains static, repetitive, or lacks attention-building change.
            """,
          extra_instructions=TIMING_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide the early visual change count in the following format: Number of early changes: #",
              "Provide exact timestamps for shot changes, visual cuts, focal shifts, text reveals, or creative transitions in the first 5 seconds.",
              "Return True only if the first-5-seconds pacing quality score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.ANNOTATIONS,
          evaluation_function="detect_quick_pacing_1st_5_secs",
          include_in_evaluation=True,
          group_by=VideoSegment.NONE,
      ),
      VideoFeature(
          id="a_supers",
          name="Supers",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.ATTRACT,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Text overlays should support attention and comprehension. Supers are strongest when they are
                readable, well-placed, visually prioritized, and help the viewer understand the core message
                without cluttering the frame.
            """,
          prompt_template="""
                Are there text overlays/supers that improve viewer attention or comprehension?

                Do not only check if text appears in the bottom third. Evaluate readability, placement,
                hierarchy, contrast, message clarity, and whether the text supports the inferred funnel intent.
                Bottom-third placement is helpful only if the text is readable and not cluttered.

                Return True if supers are clear, useful, and visually effective. Return False if supers are
                missing, too small, poorly placed, confusing, or add clutter without improving the message.
            """,
          extra_instructions=GENERAL_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide exact timestamps where supers are found and list the supers.",
              "Evaluate whether the supers are readable, prominent, and helpful for the inferred funnel intent.",
              "Return True only if super quality score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="a_supers_with_audio",
          name="Supers with Audio",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.ATTRACT,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Supers and audio should work together to reinforce the message. Exact word-for-word matching
                is strong, but contextual reinforcement can also be effective if it improves clarity and recall.
            """,
          prompt_template="""
                Do the on-screen supers and audio work together to make the message clearer and more memorable?

                Do not require only exact 1:1 verbal matching. Exact matches are ideal, but contextual support
                can pass when speech and text clearly reinforce the same idea and help viewer comprehension.

                Return True if the audio and supers reinforce each other clearly. Return False if the text and
                audio conflict, feel disconnected, or fail to support the message.
            """,
          extra_instructions=GENERAL_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide exact timestamps where supers are found and timestamps where the speech either matches or contextually supports the text.",
              "Separate exact word-for-word matches from contextual matches.",
              "Return True only if audio-super alignment quality score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="b_brand_mention_speech",
          name="Brand Mention (Speech)",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.BRAND,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                The brand name {brand_name} should be heard in a way that supports brand recall and creative intent.
                Multiple mentions can help awareness, but for conversion-focused ads, one clear brand mention near
                the action path may be sufficient if it is memorable and connected to the CTA.
            """,
          prompt_template="""
                Is the brand {brand_name} mentioned in speech with enough clarity and prominence to support
                the inferred funnel intent?

                Do not judge only by raw mention count. Evaluate timing, clarity, memorability, and whether the
                mention is connected to the key message or CTA.

                For TOFU, brand mention expectations are higher because awareness and recall are critical.
                For MOFU, the mention should support trust and product understanding.
                For BOFU, a single clear mention can be acceptable if it is strongly tied to a CTA or conversion path.

                Return True if the brand mention is clear and appropriate for the inferred funnel intent.
            """,
          extra_instructions=GENERAL_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide the exact timestamp when the brand {brand_name} is heard in speech.",
              "Count audible brand mentions and evaluate the quality/prominence of each mention.",
              "Return True only if brand mention quality score is 3/5 or higher for the inferred funnel intent.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="b_brand_mention_speech_1st_5_secs",
          name="Brand Mention (Speech) (First 5 seconds)",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.BRAND,
          video_segment=VideoSegment.FIRST_5_SECS_VIDEO,
          evaluation_criteria="""
                Early brand mention can strengthen recall, especially for TOFU / Awareness creatives.
                However, for MOFU or BOFU creatives, delayed brand mention can still be acceptable if the
                early hook establishes a strong problem, benefit, or conversion setup.
            """,
          prompt_template="""
                Is the brand {brand_name} mentioned in the first 5 seconds, or is there a strong strategic reason
                why the brand mention appears later?

                For TOFU, early spoken branding is highly valuable and should be expected unless visual branding
                is very strong. For MOFU or BOFU, delayed spoken branding can be acceptable if the opening builds
                relevance and the brand is clearly connected to the solution later.

                Return True if early spoken branding is present, or if the delayed mention is strategically effective
                for the inferred funnel intent. Return False if the absence of early brand speech weakens recall
                or clarity.
            """,
          extra_instructions=TIMING_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide the exact timestamp when the brand {brand_name} is heard in speech.",
              "If the brand is not heard in the first 5 seconds, explain whether that is acceptable for the inferred funnel intent.",
              "Return True only if early/delayed spoken brand strategy quality score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FIRST_5_SECS_VIDEO,
      ),
      VideoFeature(
          id="b_brand_visuals",
          name="Brand Visuals",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.BRAND,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Brand visuals should be visible, recognizable, and prominent enough to support the inferred
                funnel intent. Evaluate logo size, placement, duration, contrast, clarity, and whether the brand
                is integrated into the message rather than merely present.
            """,
          prompt_template="""
                Are the brand {brand_name} or brand logo visuals strong enough to support brand recognition
                for the inferred funnel intent?

                Do not disqualify the video simply because the brand or logo is found. Instead, evaluate whether
                the brand/logo is clear, recognizable, well-placed, and visually memorable.

                For TOFU, branding should be more prominent and memorable.
                For MOFU, branding should support trust and product understanding.
                For BOFU, branding can be more concise if it is clearly connected to the CTA or final action path.

                Return True if brand visuals are clear and appropriate for the inferred funnel intent.
            """,
          extra_instructions=GENERAL_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide exact timestamps when the brand {brand_name} or brand logo is visible.",
              "Estimate whether the logo is small, medium, or large; mention if it likely occupies more than 10% of the frame.",
              "Evaluate visual prominence, contrast, placement, duration, and connection to the message or CTA.",
              "Return True only if brand visual quality score is 3/5 or higher for the inferred funnel intent.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="b_brand_visuals_1st_5_secs",
          name="Brand Visuals (First 5 seconds)",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.BRAND,
          video_segment=VideoSegment.FIRST_5_SECS_VIDEO,
          evaluation_criteria="""
                Early brand visuals can strengthen awareness and recall. For TOFU creatives, early brand visibility
                is especially important. For MOFU or BOFU creatives, delayed branding can be acceptable if the
                opening builds a strong hook, problem, or action path and the brand becomes clear soon after.
            """,
          prompt_template="""
                Is the brand {brand_name} or brand logo visible in the first 5 seconds, or is delayed brand visibility
                strategically acceptable for the inferred funnel intent?

                Do not automatically reward absence of branding. Evaluate whether early or delayed branding helps
                the likely objective of the ad.

                Return True if early brand visibility is present and effective, or if delayed visibility is strategically
                acceptable for MOFU/BOFU. Return False if the lack of early branding weakens awareness, comprehension,
                or action clarity.
            """,
          extra_instructions=TIMING_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide exact timestamps when the brand {brand_name} or brand logo first appears.",
              "Explain whether the brand timing is appropriate for TOFU, MOFU, or BOFU.",
              "Return True only if brand timing/visibility quality score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FIRST_5_SECS_VIDEO,
      ),
      VideoFeature(
          id="b_product_mention_speech",
          name="Product Mention (Speech)",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.BRAND,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                The branded product names or generic product categories should be mentioned or clearly implied
                in speech when necessary for comprehension. Exact keywords are strongest, but contextual language
                can support product understanding if it clearly communicates the category or problem being solved.
            """,
          prompt_template="""
                Are any of the following products: {branded_products} or product categories:
                {branded_products_categories} mentioned or clearly implied in the speech of the video?

                Do not rely only on exact keyword matching. If the speech clearly describes the product category,
                use case, or problem-solution context, evaluate whether it helps the viewer understand what is being offered.

                Return True if the product/category is spoken or strongly and clearly implied. Return False if the
                product/category remains unclear or ambiguous.
            """,
          extra_instructions=GENERAL_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide exact timestamps when products {branded_products} or categories {branded_products_categories} are heard or clearly implied in speech.",
              "Separate exact product/category mentions from contextual implications.",
              "Only use speech/audio to answer; do not use visual elements for this feature.",
              "Return True only if product speech clarity score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="b_product_mention_speech_1st_5_secs",
          name="Product Mention (Speech) (First 5 seconds)",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.BRAND,
          video_segment=VideoSegment.FIRST_5_SECS_VIDEO,
          evaluation_criteria="""
                Early product/category mention can help comprehension, but exact timing should be judged based
                on the inferred funnel intent. TOFU may prioritize brand/hook first, MOFU may prioritize problem
                setup, and BOFU may prioritize action or utility quickly.
            """,
          prompt_template="""
                Are any of the following products: {branded_products} or product categories:
                {branded_products_categories} mentioned or clearly implied in speech in the first 5 seconds?

                If not explicitly mentioned, evaluate whether the opening speech sets up the product/category
                strongly enough for the inferred funnel intent.

                Return True if early speech clearly communicates the product/category or a highly relevant
                product problem. Return False if the category remains unclear.
            """,
          extra_instructions=TIMING_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide exact timestamps when products {branded_products} or categories {branded_products_categories} are heard or clearly implied in speech.",
              "Only use speech/audio to answer; do not use visual elements for this feature.",
              "Return True only if first-5-seconds product speech clarity score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FIRST_5_SECS_VIDEO,
      ),
      VideoFeature(
          id="b_product_mention_text",
          name="Product Mention (Text)",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.BRAND,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Product/category text should help the viewer understand what is being offered. Exact product
                naming is strong, but contextual text can be acceptable when it clearly communicates the problem,
                category, service, or user benefit.
            """,
          prompt_template="""
                Are any of the following products: {branded_products} or product categories:
                {branded_products_categories} present or clearly implied in any text or overlay?

                Do not only check exact keyword presence. Evaluate whether the text helps viewers understand
                the product/service category or the problem being solved.

                Return True if product/category text is clear, prominent, and useful for the inferred funnel intent.
                Return False if product/category understanding remains unclear.
            """,
          extra_instructions=GENERAL_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide exact timestamps when products {branded_products} or product categories {branded_products_categories} are found or clearly implied in text/overlays.",
              "Separate exact text mentions from contextual text implications.",
              "Return True only if product text clarity/prominence score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="b_product_mention_text_1st_5_secs",
          name="Product Mention (Text) (First 5 seconds)",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.BRAND,
          video_segment=VideoSegment.FIRST_5_SECS_VIDEO,
          evaluation_criteria="""
                Early product/category text can help orient the viewer, but exact requirement depends on funnel
                intent. The first 5 seconds should either clearly identify the product/category or create a strong
                setup that makes the product/service understandable shortly after.
            """,
          prompt_template="""
                Are any of the following products: {branded_products} or product categories:
                {branded_products_categories} present or clearly implied in text/overlays in the first 5 seconds?

                If not, evaluate whether the opening text still creates a strong relevant setup for the product
                or service. Return True if early text clarity is strong enough for the inferred funnel intent.
            """,
          extra_instructions=TIMING_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide exact timestamps when products {branded_products} or categories {branded_products_categories} are found or clearly implied in text/overlays.",
              "Return True only if first-5-seconds product text clarity score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FIRST_5_SECS_VIDEO,
      ),
      VideoFeature(
          id="b_product_visuals",
          name="Product Visuals",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.BRAND,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Product visuals should help the viewer understand the offer. For physical products, this can include
                holding, touching, using, or clearly showing the product. For services, relevant substitutes can include
                app screens, service personnel, branded environments, problem-solution demonstrations, or clear visual metaphors.
            """,
          prompt_template="""
                Are the products {branded_products} or product categories {branded_products_categories}
                visually represented in a way that helps viewers understand the offer?

                Do not require physical holding/touching for intangible services. For services, accept strong relevant
                substitutes such as branded app screens, customer support visuals, service personnel, UI demos, or clear
                problem-solution metaphors.

                Return True if the product/service is visually understandable and appropriate for the inferred funnel intent.
            """,
          extra_instructions=GENERAL_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide exact timestamps when products {branded_products}, product categories {branded_products_categories}, or service substitutes are visually present.",
              "Explain whether the visual representation is literal, contextual, or metaphorical.",
              "Return True only if product visual clarity score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="b_product_visuals_1st_5_secs",
          name="Product Visuals (First 5 seconds)",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.BRAND,
          video_segment=VideoSegment.FIRST_5_SECS_VIDEO,
          evaluation_criteria="""
                Product or service representation in the first 5 seconds can quickly orient the viewer. For services,
                relevant substitutes include branded apps, customer service contexts, service personnel, UI screens,
                or clear visual metaphors related to the service.
            """,
          prompt_template="""
                Are any of the following products: {branded_products} or product categories:
                {branded_products_categories} visually present or clearly represented in the first 5 seconds?

                For intangible services, accept strong substitutes or metaphors if they clearly communicate the
                service context. Return True if the early visual representation helps product/service understanding
                for the inferred funnel intent.
            """,
          extra_instructions=TIMING_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide exact timestamps when products, categories, service substitutes, or relevant metaphors are visually present in the first 5 seconds.",
              "Return True only if first-5-seconds product visual clarity score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FIRST_5_SECS_VIDEO,
      ),
      VideoFeature(
          id="c_overall_pacing",
          name="Overall Pacing",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.CONNECT,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Overall pacing should support comprehension, emotional connection, and message retention.
                No single shot should feel excessively long or slow unless it serves a clear creative purpose.
            """,
          prompt_template="""
                Does the video maintain effective overall pacing without becoming slow, confusing, or overloaded?

                Do not only check whether every shot is under 4 seconds. Evaluate whether the pace helps the viewer
                understand the story, connect with the message, and follow the action path.

                Return True if the overall pacing is clear, engaging, and appropriate for the inferred funnel intent.
            """,
          extra_instructions=TIMING_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Identify any shots that feel too long, too abrupt, or confusing.",
              "Explain whether pacing supports comprehension and connection.",
              "Return True only if overall pacing quality score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.ANNOTATIONS,
          evaluation_function="detect_overall_pacing",
          include_in_evaluation=True,
          group_by=VideoSegment.NONE,
      ),
      VideoFeature(
          id="c_presence_of_people",
          name="Presence of People",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.CONNECT,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                Human presence can build relatability and trust, but connection can also be created through
                expressive characters, creator-style delivery, hands, faces, voice, user scenarios, or emotionally
                relatable situations. Evaluate connection quality, not only headcount.
            """,
          prompt_template="""
                Does the video create human relatability or social connection through people, human presence,
                expressive characters, user scenarios, or emotionally relatable behavior?

                Do not only require three or more people in one frame. Evaluate whether the viewer is likely to
                feel connection, trust, relatability, or emotional relevance.

                Return True if connection quality is strong enough for the inferred funnel intent.
            """,
          extra_instructions=GENERAL_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide exact timestamps when people, human body parts, expressive characters, or relatable user scenarios are present.",
              "Explain whether the presence builds trust, relatability, or emotional connection.",
              "Return True only if connection quality score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="c_presence_of_people_1st_5_secs",
          name="Presence of People (First 5 seconds)",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.CONNECT,
          video_segment=VideoSegment.FIRST_5_SECS_VIDEO,
          evaluation_criteria="""
                Early human or character presence can quickly build relatability. For polished or animated ads,
                expressive non-human characters may still create connection if they behave in a human-relatable way.
            """,
          prompt_template="""
                Is there early relatability or human-like connection in the first 5 seconds through people,
                body parts, faces, expressive characters, or relatable user situations?

                Do not treat animation as automatically invalid. If an animated/cartoon character creates clear
                human-like emotion or relatable behavior, evaluate the quality of that connection.

                Return True if early connection is strong enough for the inferred funnel intent.
            """,
          extra_instructions=TIMING_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide exact timestamps when people, human-like characters, faces, body parts, or relatable scenarios are present in the first 5 seconds.",
              "Explain whether this builds early connection or simply appears visually.",
              "Return True only if first-5-seconds connection quality score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FIRST_5_SECS_VIDEO,
      ),
      VideoFeature(
          id="c_visible_face",
          name="Visible Face (First 5 seconds)",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.CONNECT,
          video_segment=VideoSegment.FIRST_5_SECS_VIDEO,
          evaluation_criteria="""
                A visible face or expressive face-like character can create early connection if it is clear,
                emotionally readable, and directed toward the viewer or central story. Human faces are strongest,
                but expressive animated characters can be considered when they clearly create human-like connection.
            """,
          prompt_template="""
                Is there a visible, emotionally readable face in the first 5 seconds that helps create connection?

                Prefer real human eye contact when present, but also evaluate expressive animated or mascot faces
                if they clearly support viewer connection. Do not reward unclear, tiny, hidden, or emotionless faces.

                Return True if face visibility/connection is strong enough for the inferred funnel intent.
            """,
          extra_instructions=TIMING_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide exact timestamps when a face is present and describe whether it is human, animated, eye-contact, expressive, or unclear.",
              "Explain whether the face improves connection for the inferred funnel intent.",
              "Return True only if visible-face connection quality score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FIRST_5_SECS_VIDEO,
      ),
      VideoFeature(
          id="c_visible_face_close_up",
          name="Visible Face (Close Up)",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.CONNECT,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                A close-up face should create emotional connection through clear expression, trust, joy,
                relief, or relevance. Close-ups are strongest when the emotion is readable and supports the message.
            """,
          prompt_template="""
                Is there a close-up of a face or expressive character that creates emotional connection?

                Do not only check for a smiling human face. Evaluate whether the close-up shows readable emotion
                such as happiness, relief, confidence, frustration, or transformation that supports the ad's message.

                Return True if the close-up creates strong connection for the inferred funnel intent.
            """,
          extra_instructions=GENERAL_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Provide exact timestamps when there is a close-up of a human face, expressive animated face, or emotionally readable character.",
              "Describe the expression and how it supports connection or message comprehension.",
              "Return True only if close-up face connection quality score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="d_audio_speech_early_1st_5_secs",
          name="Audio Early (First 5 seconds)",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.DIRECT,
          video_segment=VideoSegment.FIRST_5_SECS_VIDEO,
          evaluation_criteria="""
                Early speech/audio should quickly orient the viewer, establish the problem, deliver a hook,
                explain a benefit, or guide attention. Speech presence alone is not enough; evaluate clarity,
                urgency, and usefulness.
            """,
          prompt_template="""
                Is there useful speech in the first 5 seconds that helps guide viewer attention, understanding,
                or action?

                Do not only check whether any speech exists. Evaluate whether early speech is clear, relevant,
                attention-worthy, and appropriate for the inferred funnel intent.

                Return True if early speech meaningfully supports the ad objective.
            """,
          extra_instructions=TIMING_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Only strictly use the speech/audio of the video to answer.",
              "Provide exact timestamps and quote or summarize the early speech.",
              "Evaluate whether the speech creates attention, clarity, urgency, or problem setup.",
              "Return True only if early audio/speech quality score is 3/5 or higher.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FIRST_5_SECS_VIDEO,
      ),
      VideoFeature(
          id="d_call_to_action_speech",
          name="Call To Action (Speech)",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.DIRECT,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
                A spoken CTA should clearly guide the viewer toward the next step. Evaluate not only whether a CTA
                exists, but whether it is clear, timely, action-oriented, motivating, and appropriate for the inferred
                funnel intent.
            """,
          prompt_template="""
                Is any call to action heard or mentioned in the speech of the video, and is it effective for the
                inferred funnel intent?

                For TOFU, a soft CTA can be acceptable.
                For MOFU, the CTA should guide learning, comparison, or consideration.
                For BOFU, the CTA should be direct, urgent, and easy to act on.

                Return True if the spoken CTA is clear and strong enough for the inferred funnel intent.
            """,
          extra_instructions=GENERAL_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}.",
              "Some examples of call to actions are: {call_to_actions}",
              "Provide exact timestamps when the call to actions are heard or mentioned in speech.",
              "Evaluate CTA clarity, urgency, timing, and fit for TOFU/MOFU/BOFU.",
              "Return True only if spoken CTA quality score is 3/5 or higher for the inferred funnel intent.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
      VideoFeature(
          id="d_call_to_action_text",
          name="Call To Action (Text)",
          category=VideoFeatureCategory.LONG_FORM_ABCD,
          sub_category=VideoFeatureSubCategory.DIRECT,
          video_segment=VideoSegment.FULL_VIDEO,
          evaluation_criteria="""
              A Call To Action is visually present in the video and is clear, prominent, and actionable.
              The CTA should guide the viewer toward a next step such as buying, downloading, visiting,
              signing up, learning more, booking, ordering, subscribing, calling, or claiming an offer.
              Evaluate not only whether the CTA exists, but also whether it is visually strong enough
              to influence viewer action.
            """,
          prompt_template="""
               Is there a visible Call To Action in the video that clearly tells the viewer what action to take?

               First infer the likely funnel intent of the creative based only on the video content, speech,
               text overlays, visual hierarchy, CTA strength, offer language, urgency, and available metadata.

               Classify the likely intent as:
               - TOFU / Awareness: mainly focused on brand recall, emotional hook, broad visibility, or memorability.
               - MOFU / Consideration: mainly focused on explaining benefits, solving a problem, building trust,
                 or helping the viewer evaluate the product.
               - BOFU / Conversion: mainly focused on immediate action, strong CTA, offer, urgency, sign-up,
                 purchase, booking, app install, trial, call, or direct response.

               Then evaluate the CTA based on that inferred funnel intent:
               - For TOFU, the CTA can be softer and less dominant if the ad is mainly designed for awareness.
               - For MOFU, the CTA should clearly guide the viewer toward exploration, learning, comparison,
                 or consideration.
               - For BOFU, the CTA should be highly visible, direct, urgent, and easy to act on.

               Do not judge only by whether the CTA is inside a button or box.
               Instead, evaluate the CTA's performance quality based on:
               1. Clarity: Is the requested action easy to understand?
               2. Prominence: Is the CTA visually noticeable and not hidden?
               3. Urgency or motivation: Does it give the viewer a reason to act?
               4. Visual hierarchy: Is the CTA easy to distinguish from other text or clutter?
               5. Funnel fit: Is the CTA strong enough for the inferred funnel intent?

               Return True if the CTA is clear and reasonably prominent for the inferred funnel intent.
               Return False if the CTA is missing, vague, too small, hidden, low contrast, lost in clutter,
               or too weak for the likely funnel intent.
            """,
          extra_instructions=GENERAL_CREATIVE_INSTRUCTIONS + [
              "Consider the following criteria for your answer: {criteria}",
              "Some examples of call to actions are: {call_to_actions}",
              "Look through each frame in the video carefully and answer the question.",
              "Provide the exact timestamp when the call to action is detected in any text overlay in the video.",
              "State the inferred funnel intent as TOFU, MOFU, or BOFU, and explain why.",
              "Evaluate whether the CTA strength is appropriate for that inferred funnel intent.",
              "Mention CTA Funnel Fit as Poor, Acceptable, Strong, or Excellent.",
              "Return True only if the CTA Prominence Score is 3/5 or higher and the CTA is appropriate for the inferred funnel intent.",
          ],
          evaluation_method=EvaluationMethod.LLMS,
          evaluation_function="",
          include_in_evaluation=True,
          group_by=VideoSegment.FULL_VIDEO,
      ),
  ]

  return feature_configs
