class FeedbackAgent:

    async def process(
        self,
        user_id,
        report_id,
        rating,
        comment
    ):

        logger.info(
            f"Received feedback from user {user_id}"
        )

        return {

            "user_id": user_id,

            "report_id": report_id,

            "rating": rating,

            "comment": comment
        }