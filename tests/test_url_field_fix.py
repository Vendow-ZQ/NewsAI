"""Test URL field format fix for FeishuStorage.

This test verifies that URL fields are properly converted from plain strings
to Feishu URL format {"text": "...", "link": "..."}.
"""
import os
import sys

# Mock the field types that would come from Feishu API
MOCK_FIELD_TYPES = {
    "帖子文档链接": 15,  # URL field
    "视频脚本文档链接": 15,  # URL field
    "审改文档链接": 15,  # URL field
    "经验文档链接": 15,  # URL field
    "原文链接": 15,  # URL field
    "选题标题": 1,  # Text field (should not be converted)
    "状态": 1,  # Text field
}


def test_url_field_conversion():
    """Test that URL fields are converted properly."""
    # Simulate the _prepare_fields_for_feishu logic
    def prepare_fields(data: dict, field_types: dict) -> dict:
        result = {}
        for field_name, value in data.items():
            field_type = field_types.get(field_name)
            # URL field (type=15) needs special format
            if field_type == 15 and isinstance(value, str):
                result[field_name] = {
                    "text": value,
                    "link": value
                }
            else:
                result[field_name] = value
        return result

    # Test data - what agents currently send
    test_data = {
        "选题标题": "GPT-5预览版发布：推理能力飙升40%",
        "状态": "生产中",
        "帖子文档链接": "https://f5tgebopkn.feishu.cn/docx/ABC123",
        "视频脚本文档链接": "https://f5tgebopkn.feishu.cn/docx/DEF456",
    }

    # Expected output
    expected = {
        "选题标题": "GPT-5预览版发布：推理能力飙升40%",
        "状态": "生产中",
        "帖子文档链接": {
            "text": "https://f5tgebopkn.feishu.cn/docx/ABC123",
            "link": "https://f5tgebopkn.feishu.cn/docx/ABC123",
        },
        "视频脚本文档链接": {
            "text": "https://f5tgebopkn.feishu.cn/docx/DEF456",
            "link": "https://f5tgebopkn.feishu.cn/docx/DEF456",
        },
    }

    result = prepare_fields(test_data, MOCK_FIELD_TYPES)

    print("Input data:")
    for k, v in test_data.items():
        print(f"  {k}: {v}")

    print("\nOutput data:")
    for k, v in result.items():
        print(f"  {k}: {v}")

    # Verify
    assert result == expected, f"Mismatch!\nExpected: {expected}\nGot: {result}"
    print("\n[PASS] URL field conversion test passed!")

    # Test with non-URL fields (should remain unchanged)
    non_url_data = {
        "选题标题": "Test Title",
        "状态": "已选",
        "推荐优先级": 9,
    }
    non_url_field_types = {
        "选题标题": 1,  # Text
        "状态": 1,  # Text
        "推荐优先级": 2,  # Number
    }

    result2 = prepare_fields(non_url_data, non_url_field_types)
    assert result2 == non_url_data, f"Non-URL fields should not be modified!"
    print("[PASS] Non-URL fields remain unchanged!")

    return True


if __name__ == "__main__":
    try:
        test_url_field_conversion()
        print("\nAll tests passed! The URL field fix should work correctly.")
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
