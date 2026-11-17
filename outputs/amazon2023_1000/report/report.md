# 差评归因报告

分析评论数：1000。

## 全量归因分布（按优先级排序）

1. `quality_durability`：289 条（28.9%），平均严重度 3.554，平均置信度 0.926，优先级 950.561
2. `performance_functionality`：226 条（22.6%），平均严重度 3.456，平均置信度 0.913，优先级 712.714
3. `size_fit_design`：136 条（13.6%），平均严重度 2.897，平均置信度 0.926，优先级 364.653
4. `description_expectation_gap`：133 条（13.3%），平均严重度 3.023，平均置信度 0.899，优先级 361.588
5. `safety_health`：63 条（6.3%），平均严重度 4.429，平均置信度 0.923，优先级 257.654
6. `usability_setup`：34 条（3.4%），平均严重度 3.029，平均置信度 0.898，优先级 92.458
7. `value_for_money`：36 条（3.6%），平均严重度 2.722，平均置信度 0.881，优先级 86.349
8. `delivery_packaging`：26 条（2.6%），平均严重度 3.423，平均置信度 0.918，优先级 81.743
9. `wrong_item_counterfeit`：16 条（1.6%），平均严重度 3.688，平均置信度 0.914，优先级 53.948
10. `other`：25 条（2.5%），平均严重度 1.72，平均置信度 0.803，优先级 34.52
11. `customer_service_return`：6 条（0.6%），平均严重度 3.833，平均置信度 0.875，优先级 20.125
12. `unclear`：10 条（1.0%），平均严重度 2.0，平均置信度 0.725，优先级 14.5

## 品类 × 归因

| 品类 | 差评数 | 首位原因 | 第二位原因 | 第三位原因 |
| --- | --- | --- | --- | --- |
| All_Beauty | 250 | performance_functionality（67，26.8%） | quality_durability（63，25.2%） | description_expectation_gap（40，16.0%） |
| Appliances | 250 | quality_durability（75，30.0%） | performance_functionality（72，28.8%） | size_fit_design（45，18.0%） |
| Home_and_Kitchen | 250 | quality_durability（96，38.4%） | performance_functionality（37，14.8%） | description_expectation_gap（32，12.8%） |
| Pet_Supplies | 250 | quality_durability（55，22.0%） | performance_functionality（50，20.0%） | description_expectation_gap（35，14.0%） |

## 解释边界

优先级 = 评论数 × 平均严重度 × 平均置信度。它用于安排人工复核和改进顺序，不能证明某个原因是客观产品缺陷。建议优先复核置信度低于 0.6 的记录，并从每个一级原因中抽样核对证据片段。
