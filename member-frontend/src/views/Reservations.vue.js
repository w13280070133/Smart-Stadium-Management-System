import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import dayjs from "dayjs";
import http from "../utils/http";
const loading = ref(false);
const list = ref([]);
const statusFilter = ref("all");
const reserveDialogVisible = ref(false);
const submitLoading = ref(false);
const courts = ref([]);
const cancelLoading = ref(null);
const reserveForm = ref({
    court_id: null,
    date: null,
    start_time: "09:00",
    end_time: "10:00",
    remark: "",
});
const formatMoney = (val) => {
    const n = Number(val);
    if (Number.isNaN(n))
        return "0.00";
    return n.toFixed(2);
};
const filteredList = computed(() => {
    if (statusFilter.value === "all")
        return list.value;
    return list.value.filter((item) => {
        const raw = (item.raw_status || item.status || "").toLowerCase();
        if (statusFilter.value === "active") {
            return (raw.includes("reserved") ||
                raw.includes("using") ||
                raw.includes("pending") ||
                raw.includes("已预约"));
        }
        if (statusFilter.value === "done") {
            return raw.includes("completed") || raw.includes("done") || raw.includes("已完成");
        }
        if (statusFilter.value === "closed") {
            return (raw.includes("cancel") ||
                raw.includes("cancelled") ||
                raw.includes("refunded") ||
                raw.includes("已取消") ||
                raw.includes("已退款"));
        }
        return true;
    });
});
/**
 * 兼容多种返回结构：
 * - 直接数组 [...]
 * - { data: [...] }
 * - { code, data: [...] }
 * - { data: { code, data: [...] } }
 */
const extractList = (res) => {
    if (Array.isArray(res))
        return res;
    if (res && Array.isArray(res.data))
        return res.data;
    if (res && res.data && Array.isArray(res.data.data))
        return res.data.data;
    if (res && Array.isArray(res.items))
        return res.items;
    if (res && res.data && Array.isArray(res.data.items))
        return res.data.items;
    return [];
};
const loadReservations = async () => {
    loading.value = true;
    try {
        const res = await http.get("/member/reservations");
        const data = extractList(res);
        list.value = data.map((item) => {
            const start = item.start_time || "";
            const end = item.end_time || "";
            const timeRange = start && end ? `${start} - ${end}` : start || end || "";
            return {
                id: item.id,
                court_name: item.court_name || "",
                date: item.date || "",
                start_time: item.start_time || "",
                end_time: item.end_time || "",
                time_range: timeRange,
                amount: Number(item.amount || 0),
                status: item.status || "—",
                raw_status: String(item.raw_status || item.status || ""),
                remark: item.remark || "",
                created_at: item.created_at || "",
            };
        });
    }
    catch (err) {
        console.error(err);
        ElMessage.error("获取我的预约失败");
    }
    finally {
        loading.value = false;
    }
};
const loadCourts = async () => {
    try {
        const res = await http.get("/courts");
        const data = extractList(res);
        courts.value = data.map((c) => ({
            id: c.id,
            name: c.name,
        }));
    }
    catch (err) {
        console.error(err);
        ElMessage.error("获取场地列表失败");
    }
};
const openReserveDialog = async () => {
    reserveDialogVisible.value = true;
    if (!courts.value.length) {
        await loadCourts();
    }
};
const canCancelReservation = (row) => {
    const raw = (row.raw_status || row.status || "").toLowerCase();
    if (!row.id)
        return false;
    if (!raw)
        return true;
    if (raw.includes("取消") ||
        raw.includes("cancel") ||
        raw.includes("refunded") ||
        raw.includes("退款") ||
        raw.includes("completed") ||
        raw.includes("done") ||
        raw.includes("已完成")) {
        return false;
    }
    const datePart = row.date || "";
    let composed = datePart;
    if (row.start_time) {
        if (dayjs(datePart).isValid() && datePart.includes(":")) {
            composed = datePart;
        }
        else {
            composed = `${datePart} ${row.start_time}`;
        }
    }
    const startMoment = dayjs(composed);
    if (startMoment.isValid() && startMoment.isBefore(dayjs())) {
        return false;
    }
    return true;
};
const cancelReservation = async (row) => {
    if (!canCancelReservation(row))
        return;
    cancelLoading.value = row.id;
    try {
        await http.post(`/member/reservations/${row.id}/cancel`, {
            remark: row.remark || "",
        });
        ElMessage.success("预约已取消并退款");
        loadReservations();
    }
    catch (err) {
        const msg = err?.response?.data?.detail ||
            err?.message ||
            "取消失败，请稍后再试";
        ElMessage.error(msg);
    }
    finally {
        cancelLoading.value = null;
    }
};
const submitReserve = async () => {
    if (!reserveForm.value.court_id) {
        ElMessage.warning("请选择场地");
        return;
    }
    if (!reserveForm.value.date) {
        ElMessage.warning("请选择日期");
        return;
    }
    if (!reserveForm.value.start_time || !reserveForm.value.end_time) {
        ElMessage.warning("请选择开始和结束时间");
        return;
    }
    const dateStr = dayjs(reserveForm.value.date).format("YYYY-MM-DD");
    const payload = {
        court_id: reserveForm.value.court_id,
        date: dateStr,
        start_time: reserveForm.value.start_time,
        end_time: reserveForm.value.end_time,
        remark: reserveForm.value.remark || "",
    };
    submitLoading.value = true;
    try {
        await http.post("/member/reservations", payload);
        ElMessage.success("预约成功");
        reserveDialogVisible.value = false;
        loadReservations();
    }
    catch (err) {
        console.error(err);
        const msg = err?.response?.data?.detail ||
            err?.message ||
            "预约失败，请稍后重试";
        ElMessage.error(msg);
    }
    finally {
        submitLoading.value = false;
    }
};
onMounted(() => {
    loadReservations();
});
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['card-header']} */ ;
/** @type {__VLS_StyleScopedClasses['card-header']} */ ;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "page" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "page-header" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
__VLS_asFunctionalElement(__VLS_intrinsics.h2, __VLS_intrinsics.h2)({});
__VLS_asFunctionalElement(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "sub-title" },
});
const __VLS_0 = {}.ElButton;
/** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
// @ts-ignore
ElButton;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
    ...{ 'onClick': {} },
    type: "primary",
    size: "large",
}));
const __VLS_2 = __VLS_1({
    ...{ 'onClick': {} },
    type: "primary",
    size: "large",
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
let __VLS_4;
let __VLS_5;
const __VLS_6 = ({ click: {} },
    { onClick: (__VLS_ctx.openReserveDialog) });
const { default: __VLS_7 } = __VLS_3.slots;
// @ts-ignore
[openReserveDialog,];
var __VLS_3;
const __VLS_8 = {}.ElCard;
/** @type {[typeof __VLS_components.ElCard, typeof __VLS_components.elCard, typeof __VLS_components.ElCard, typeof __VLS_components.elCard, ]} */ ;
// @ts-ignore
ElCard;
// @ts-ignore
const __VLS_9 = __VLS_asFunctionalComponent(__VLS_8, new __VLS_8({
    ...{ class: "card" },
    shadow: "never",
}));
const __VLS_10 = __VLS_9({
    ...{ class: "card" },
    shadow: "never",
}, ...__VLS_functionalComponentArgsRest(__VLS_9));
const { default: __VLS_12 } = __VLS_11.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "card-header" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "title" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "actions" },
});
const __VLS_13 = {}.ElSelect;
/** @type {[typeof __VLS_components.ElSelect, typeof __VLS_components.elSelect, typeof __VLS_components.ElSelect, typeof __VLS_components.elSelect, ]} */ ;
// @ts-ignore
ElSelect;
// @ts-ignore
const __VLS_14 = __VLS_asFunctionalComponent(__VLS_13, new __VLS_13({
    modelValue: (__VLS_ctx.statusFilter),
    size: "small",
    ...{ style: {} },
}));
const __VLS_15 = __VLS_14({
    modelValue: (__VLS_ctx.statusFilter),
    size: "small",
    ...{ style: {} },
}, ...__VLS_functionalComponentArgsRest(__VLS_14));
const { default: __VLS_17 } = __VLS_16.slots;
// @ts-ignore
[statusFilter,];
const __VLS_18 = {}.ElOption;
/** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
// @ts-ignore
ElOption;
// @ts-ignore
const __VLS_19 = __VLS_asFunctionalComponent(__VLS_18, new __VLS_18({
    label: "全部状态",
    value: "all",
}));
const __VLS_20 = __VLS_19({
    label: "全部状态",
    value: "all",
}, ...__VLS_functionalComponentArgsRest(__VLS_19));
const __VLS_23 = {}.ElOption;
/** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
// @ts-ignore
ElOption;
// @ts-ignore
const __VLS_24 = __VLS_asFunctionalComponent(__VLS_23, new __VLS_23({
    label: "已预约 / 使用中",
    value: "active",
}));
const __VLS_25 = __VLS_24({
    label: "已预约 / 使用中",
    value: "active",
}, ...__VLS_functionalComponentArgsRest(__VLS_24));
const __VLS_28 = {}.ElOption;
/** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
// @ts-ignore
ElOption;
// @ts-ignore
const __VLS_29 = __VLS_asFunctionalComponent(__VLS_28, new __VLS_28({
    label: "已完成",
    value: "done",
}));
const __VLS_30 = __VLS_29({
    label: "已完成",
    value: "done",
}, ...__VLS_functionalComponentArgsRest(__VLS_29));
const __VLS_33 = {}.ElOption;
/** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
// @ts-ignore
ElOption;
// @ts-ignore
const __VLS_34 = __VLS_asFunctionalComponent(__VLS_33, new __VLS_33({
    label: "已取消 / 已退款",
    value: "closed",
}));
const __VLS_35 = __VLS_34({
    label: "已取消 / 已退款",
    value: "closed",
}, ...__VLS_functionalComponentArgsRest(__VLS_34));
var __VLS_16;
const __VLS_38 = {}.ElButton;
/** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
// @ts-ignore
ElButton;
// @ts-ignore
const __VLS_39 = __VLS_asFunctionalComponent(__VLS_38, new __VLS_38({
    ...{ 'onClick': {} },
    size: "small",
    loading: (__VLS_ctx.loading),
}));
const __VLS_40 = __VLS_39({
    ...{ 'onClick': {} },
    size: "small",
    loading: (__VLS_ctx.loading),
}, ...__VLS_functionalComponentArgsRest(__VLS_39));
let __VLS_42;
let __VLS_43;
const __VLS_44 = ({ click: {} },
    { onClick: (__VLS_ctx.loadReservations) });
const { default: __VLS_45 } = __VLS_41.slots;
// @ts-ignore
[loading, loadReservations,];
var __VLS_41;
const __VLS_46 = {}.ElTable;
/** @type {[typeof __VLS_components.ElTable, typeof __VLS_components.elTable, typeof __VLS_components.ElTable, typeof __VLS_components.elTable, ]} */ ;
// @ts-ignore
ElTable;
// @ts-ignore
const __VLS_47 = __VLS_asFunctionalComponent(__VLS_46, new __VLS_46({
    data: (__VLS_ctx.filteredList),
    border: true,
    ...{ style: {} },
    emptyText: "暂无预约记录",
}));
const __VLS_48 = __VLS_47({
    data: (__VLS_ctx.filteredList),
    border: true,
    ...{ style: {} },
    emptyText: "暂无预约记录",
}, ...__VLS_functionalComponentArgsRest(__VLS_47));
__VLS_asFunctionalDirective(__VLS_directives.vLoading)(null, { ...__VLS_directiveBindingRestFields, value: (__VLS_ctx.loading) }, null, null);
const { default: __VLS_50 } = __VLS_49.slots;
// @ts-ignore
[loading, filteredList, vLoading,];
const __VLS_51 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_52 = __VLS_asFunctionalComponent(__VLS_51, new __VLS_51({
    type: "index",
    width: "60",
    label: "#",
}));
const __VLS_53 = __VLS_52({
    type: "index",
    width: "60",
    label: "#",
}, ...__VLS_functionalComponentArgsRest(__VLS_52));
const __VLS_56 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_57 = __VLS_asFunctionalComponent(__VLS_56, new __VLS_56({
    prop: "court_name",
    label: "场地",
    minWidth: "120",
}));
const __VLS_58 = __VLS_57({
    prop: "court_name",
    label: "场地",
    minWidth: "120",
}, ...__VLS_functionalComponentArgsRest(__VLS_57));
const __VLS_61 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_62 = __VLS_asFunctionalComponent(__VLS_61, new __VLS_61({
    prop: "date",
    label: "日期",
    minWidth: "120",
}));
const __VLS_63 = __VLS_62({
    prop: "date",
    label: "日期",
    minWidth: "120",
}, ...__VLS_functionalComponentArgsRest(__VLS_62));
const __VLS_66 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_67 = __VLS_asFunctionalComponent(__VLS_66, new __VLS_66({
    prop: "time_range",
    label: "时间",
    minWidth: "140",
}));
const __VLS_68 = __VLS_67({
    prop: "time_range",
    label: "时间",
    minWidth: "140",
}, ...__VLS_functionalComponentArgsRest(__VLS_67));
const __VLS_71 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_72 = __VLS_asFunctionalComponent(__VLS_71, new __VLS_71({
    prop: "amount",
    label: "金额（元）",
    minWidth: "120",
}));
const __VLS_73 = __VLS_72({
    prop: "amount",
    label: "金额（元）",
    minWidth: "120",
}, ...__VLS_functionalComponentArgsRest(__VLS_72));
const { default: __VLS_75 } = __VLS_74.slots;
{
    const { default: __VLS_76 } = __VLS_74.slots;
    const [{ row }] = __VLS_getSlotParameters(__VLS_76);
    __VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    (__VLS_ctx.formatMoney(row.amount));
    // @ts-ignore
    [formatMoney,];
}
var __VLS_74;
const __VLS_77 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_78 = __VLS_asFunctionalComponent(__VLS_77, new __VLS_77({
    prop: "status",
    label: "状态",
    minWidth: "100",
}));
const __VLS_79 = __VLS_78({
    prop: "status",
    label: "状态",
    minWidth: "100",
}, ...__VLS_functionalComponentArgsRest(__VLS_78));
const { default: __VLS_81 } = __VLS_80.slots;
{
    const { default: __VLS_82 } = __VLS_80.slots;
    const [{ row }] = __VLS_getSlotParameters(__VLS_82);
    const __VLS_83 = {}.ElTag;
    /** @type {[typeof __VLS_components.ElTag, typeof __VLS_components.elTag, typeof __VLS_components.ElTag, typeof __VLS_components.elTag, ]} */ ;
    // @ts-ignore
    ElTag;
    // @ts-ignore
    const __VLS_84 = __VLS_asFunctionalComponent(__VLS_83, new __VLS_83({
        size: "small",
    }));
    const __VLS_85 = __VLS_84({
        size: "small",
    }, ...__VLS_functionalComponentArgsRest(__VLS_84));
    const { default: __VLS_87 } = __VLS_86.slots;
    (row.status || "—");
    var __VLS_86;
}
var __VLS_80;
const __VLS_88 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_89 = __VLS_asFunctionalComponent(__VLS_88, new __VLS_88({
    prop: "created_at",
    label: "预约时间",
    minWidth: "160",
}));
const __VLS_90 = __VLS_89({
    prop: "created_at",
    label: "预约时间",
    minWidth: "160",
}, ...__VLS_functionalComponentArgsRest(__VLS_89));
const __VLS_93 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_94 = __VLS_asFunctionalComponent(__VLS_93, new __VLS_93({
    prop: "remark",
    label: "备注",
    minWidth: "160",
    showOverflowTooltip: true,
}));
const __VLS_95 = __VLS_94({
    prop: "remark",
    label: "备注",
    minWidth: "160",
    showOverflowTooltip: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_94));
const __VLS_98 = {}.ElTableColumn;
/** @type {[typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, typeof __VLS_components.ElTableColumn, typeof __VLS_components.elTableColumn, ]} */ ;
// @ts-ignore
ElTableColumn;
// @ts-ignore
const __VLS_99 = __VLS_asFunctionalComponent(__VLS_98, new __VLS_98({
    label: "操作",
    width: "120",
}));
const __VLS_100 = __VLS_99({
    label: "操作",
    width: "120",
}, ...__VLS_functionalComponentArgsRest(__VLS_99));
const { default: __VLS_102 } = __VLS_101.slots;
{
    const { default: __VLS_103 } = __VLS_101.slots;
    const [{ row }] = __VLS_getSlotParameters(__VLS_103);
    const __VLS_104 = {}.ElPopconfirm;
    /** @type {[typeof __VLS_components.ElPopconfirm, typeof __VLS_components.elPopconfirm, typeof __VLS_components.ElPopconfirm, typeof __VLS_components.elPopconfirm, ]} */ ;
    // @ts-ignore
    ElPopconfirm;
    // @ts-ignore
    const __VLS_105 = __VLS_asFunctionalComponent(__VLS_104, new __VLS_104({
        ...{ 'onConfirm': {} },
        title: "确定要取消该预约吗？退款会原路退回余额",
        confirmButtonText: "确认取消",
        cancelButtonText: "再想想",
        disabled: (!__VLS_ctx.canCancelReservation(row)),
    }));
    const __VLS_106 = __VLS_105({
        ...{ 'onConfirm': {} },
        title: "确定要取消该预约吗？退款会原路退回余额",
        confirmButtonText: "确认取消",
        cancelButtonText: "再想想",
        disabled: (!__VLS_ctx.canCancelReservation(row)),
    }, ...__VLS_functionalComponentArgsRest(__VLS_105));
    let __VLS_108;
    let __VLS_109;
    const __VLS_110 = ({ confirm: {} },
        { onConfirm: (...[$event]) => {
                __VLS_ctx.cancelReservation(row);
                // @ts-ignore
                [canCancelReservation, cancelReservation,];
            } });
    const { default: __VLS_111 } = __VLS_107.slots;
    {
        const { reference: __VLS_112 } = __VLS_107.slots;
        const __VLS_113 = {}.ElButton;
        /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
        // @ts-ignore
        ElButton;
        // @ts-ignore
        const __VLS_114 = __VLS_asFunctionalComponent(__VLS_113, new __VLS_113({
            link: true,
            type: "danger",
            size: "small",
            disabled: (!__VLS_ctx.canCancelReservation(row)),
            loading: (__VLS_ctx.cancelLoading === row.id),
        }));
        const __VLS_115 = __VLS_114({
            link: true,
            type: "danger",
            size: "small",
            disabled: (!__VLS_ctx.canCancelReservation(row)),
            loading: (__VLS_ctx.cancelLoading === row.id),
        }, ...__VLS_functionalComponentArgsRest(__VLS_114));
        const { default: __VLS_117 } = __VLS_116.slots;
        // @ts-ignore
        [canCancelReservation, cancelLoading,];
        var __VLS_116;
    }
    var __VLS_107;
}
var __VLS_101;
var __VLS_49;
var __VLS_11;
const __VLS_118 = {}.ElDialog;
/** @type {[typeof __VLS_components.ElDialog, typeof __VLS_components.elDialog, typeof __VLS_components.ElDialog, typeof __VLS_components.elDialog, ]} */ ;
// @ts-ignore
ElDialog;
// @ts-ignore
const __VLS_119 = __VLS_asFunctionalComponent(__VLS_118, new __VLS_118({
    modelValue: (__VLS_ctx.reserveDialogVisible),
    title: "我要预约",
    width: "480px",
    destroyOnClose: true,
}));
const __VLS_120 = __VLS_119({
    modelValue: (__VLS_ctx.reserveDialogVisible),
    title: "我要预约",
    width: "480px",
    destroyOnClose: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_119));
const { default: __VLS_122 } = __VLS_121.slots;
// @ts-ignore
[reserveDialogVisible,];
const __VLS_123 = {}.ElForm;
/** @type {[typeof __VLS_components.ElForm, typeof __VLS_components.elForm, typeof __VLS_components.ElForm, typeof __VLS_components.elForm, ]} */ ;
// @ts-ignore
ElForm;
// @ts-ignore
const __VLS_124 = __VLS_asFunctionalComponent(__VLS_123, new __VLS_123({
    model: (__VLS_ctx.reserveForm),
    labelWidth: "80px",
}));
const __VLS_125 = __VLS_124({
    model: (__VLS_ctx.reserveForm),
    labelWidth: "80px",
}, ...__VLS_functionalComponentArgsRest(__VLS_124));
const { default: __VLS_127 } = __VLS_126.slots;
// @ts-ignore
[reserveForm,];
const __VLS_128 = {}.ElFormItem;
/** @type {[typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, ]} */ ;
// @ts-ignore
ElFormItem;
// @ts-ignore
const __VLS_129 = __VLS_asFunctionalComponent(__VLS_128, new __VLS_128({
    label: "场地",
}));
const __VLS_130 = __VLS_129({
    label: "场地",
}, ...__VLS_functionalComponentArgsRest(__VLS_129));
const { default: __VLS_132 } = __VLS_131.slots;
const __VLS_133 = {}.ElSelect;
/** @type {[typeof __VLS_components.ElSelect, typeof __VLS_components.elSelect, typeof __VLS_components.ElSelect, typeof __VLS_components.elSelect, ]} */ ;
// @ts-ignore
ElSelect;
// @ts-ignore
const __VLS_134 = __VLS_asFunctionalComponent(__VLS_133, new __VLS_133({
    modelValue: (__VLS_ctx.reserveForm.court_id),
    placeholder: "请选择场地",
    ...{ style: {} },
}));
const __VLS_135 = __VLS_134({
    modelValue: (__VLS_ctx.reserveForm.court_id),
    placeholder: "请选择场地",
    ...{ style: {} },
}, ...__VLS_functionalComponentArgsRest(__VLS_134));
const { default: __VLS_137 } = __VLS_136.slots;
// @ts-ignore
[reserveForm,];
for (const [c] of __VLS_getVForSourceType((__VLS_ctx.courts))) {
    // @ts-ignore
    [courts,];
    const __VLS_138 = {}.ElOption;
    /** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
    // @ts-ignore
    ElOption;
    // @ts-ignore
    const __VLS_139 = __VLS_asFunctionalComponent(__VLS_138, new __VLS_138({
        key: (c.id),
        label: (c.name),
        value: (c.id),
    }));
    const __VLS_140 = __VLS_139({
        key: (c.id),
        label: (c.name),
        value: (c.id),
    }, ...__VLS_functionalComponentArgsRest(__VLS_139));
}
var __VLS_136;
var __VLS_131;
const __VLS_143 = {}.ElFormItem;
/** @type {[typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, ]} */ ;
// @ts-ignore
ElFormItem;
// @ts-ignore
const __VLS_144 = __VLS_asFunctionalComponent(__VLS_143, new __VLS_143({
    label: "日期",
}));
const __VLS_145 = __VLS_144({
    label: "日期",
}, ...__VLS_functionalComponentArgsRest(__VLS_144));
const { default: __VLS_147 } = __VLS_146.slots;
const __VLS_148 = {}.ElDatePicker;
/** @type {[typeof __VLS_components.ElDatePicker, typeof __VLS_components.elDatePicker, ]} */ ;
// @ts-ignore
ElDatePicker;
// @ts-ignore
const __VLS_149 = __VLS_asFunctionalComponent(__VLS_148, new __VLS_148({
    modelValue: (__VLS_ctx.reserveForm.date),
    type: "date",
    placeholder: "选择日期",
    ...{ style: {} },
}));
const __VLS_150 = __VLS_149({
    modelValue: (__VLS_ctx.reserveForm.date),
    type: "date",
    placeholder: "选择日期",
    ...{ style: {} },
}, ...__VLS_functionalComponentArgsRest(__VLS_149));
// @ts-ignore
[reserveForm,];
var __VLS_146;
const __VLS_153 = {}.ElFormItem;
/** @type {[typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, ]} */ ;
// @ts-ignore
ElFormItem;
// @ts-ignore
const __VLS_154 = __VLS_asFunctionalComponent(__VLS_153, new __VLS_153({
    label: "时间段",
}));
const __VLS_155 = __VLS_154({
    label: "时间段",
}, ...__VLS_functionalComponentArgsRest(__VLS_154));
const { default: __VLS_157 } = __VLS_156.slots;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "time-row" },
});
const __VLS_158 = {}.ElTimeSelect;
/** @type {[typeof __VLS_components.ElTimeSelect, typeof __VLS_components.elTimeSelect, ]} */ ;
// @ts-ignore
ElTimeSelect;
// @ts-ignore
const __VLS_159 = __VLS_asFunctionalComponent(__VLS_158, new __VLS_158({
    modelValue: (__VLS_ctx.reserveForm.start_time),
    placeholder: "开始时间",
    start: "06:00",
    end: "23:00",
    step: "00:30",
    ...{ style: {} },
}));
const __VLS_160 = __VLS_159({
    modelValue: (__VLS_ctx.reserveForm.start_time),
    placeholder: "开始时间",
    start: "06:00",
    end: "23:00",
    step: "00:30",
    ...{ style: {} },
}, ...__VLS_functionalComponentArgsRest(__VLS_159));
// @ts-ignore
[reserveForm,];
__VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "time-sep" },
});
const __VLS_163 = {}.ElTimeSelect;
/** @type {[typeof __VLS_components.ElTimeSelect, typeof __VLS_components.elTimeSelect, ]} */ ;
// @ts-ignore
ElTimeSelect;
// @ts-ignore
const __VLS_164 = __VLS_asFunctionalComponent(__VLS_163, new __VLS_163({
    modelValue: (__VLS_ctx.reserveForm.end_time),
    placeholder: "结束时间",
    start: "06:00",
    end: "23:00",
    step: "00:30",
    ...{ style: {} },
}));
const __VLS_165 = __VLS_164({
    modelValue: (__VLS_ctx.reserveForm.end_time),
    placeholder: "结束时间",
    start: "06:00",
    end: "23:00",
    step: "00:30",
    ...{ style: {} },
}, ...__VLS_functionalComponentArgsRest(__VLS_164));
// @ts-ignore
[reserveForm,];
var __VLS_156;
const __VLS_168 = {}.ElFormItem;
/** @type {[typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, ]} */ ;
// @ts-ignore
ElFormItem;
// @ts-ignore
const __VLS_169 = __VLS_asFunctionalComponent(__VLS_168, new __VLS_168({
    label: "备注",
}));
const __VLS_170 = __VLS_169({
    label: "备注",
}, ...__VLS_functionalComponentArgsRest(__VLS_169));
const { default: __VLS_172 } = __VLS_171.slots;
const __VLS_173 = {}.ElInput;
/** @type {[typeof __VLS_components.ElInput, typeof __VLS_components.elInput, ]} */ ;
// @ts-ignore
ElInput;
// @ts-ignore
const __VLS_174 = __VLS_asFunctionalComponent(__VLS_173, new __VLS_173({
    modelValue: (__VLS_ctx.reserveForm.remark),
    type: "textarea",
    rows: (2),
    placeholder: "可填写使用人、特殊说明等（可选）",
}));
const __VLS_175 = __VLS_174({
    modelValue: (__VLS_ctx.reserveForm.remark),
    type: "textarea",
    rows: (2),
    placeholder: "可填写使用人、特殊说明等（可选）",
}, ...__VLS_functionalComponentArgsRest(__VLS_174));
// @ts-ignore
[reserveForm,];
var __VLS_171;
var __VLS_126;
{
    const { footer: __VLS_178 } = __VLS_121.slots;
    const __VLS_179 = {}.ElButton;
    /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
    // @ts-ignore
    ElButton;
    // @ts-ignore
    const __VLS_180 = __VLS_asFunctionalComponent(__VLS_179, new __VLS_179({
        ...{ 'onClick': {} },
    }));
    const __VLS_181 = __VLS_180({
        ...{ 'onClick': {} },
    }, ...__VLS_functionalComponentArgsRest(__VLS_180));
    let __VLS_183;
    let __VLS_184;
    const __VLS_185 = ({ click: {} },
        { onClick: (...[$event]) => {
                __VLS_ctx.reserveDialogVisible = false;
                // @ts-ignore
                [reserveDialogVisible,];
            } });
    const { default: __VLS_186 } = __VLS_182.slots;
    var __VLS_182;
    const __VLS_187 = {}.ElButton;
    /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
    // @ts-ignore
    ElButton;
    // @ts-ignore
    const __VLS_188 = __VLS_asFunctionalComponent(__VLS_187, new __VLS_187({
        ...{ 'onClick': {} },
        type: "primary",
        loading: (__VLS_ctx.submitLoading),
    }));
    const __VLS_189 = __VLS_188({
        ...{ 'onClick': {} },
        type: "primary",
        loading: (__VLS_ctx.submitLoading),
    }, ...__VLS_functionalComponentArgsRest(__VLS_188));
    let __VLS_191;
    let __VLS_192;
    const __VLS_193 = ({ click: {} },
        { onClick: (__VLS_ctx.submitReserve) });
    const { default: __VLS_194 } = __VLS_190.slots;
    // @ts-ignore
    [submitLoading, submitReserve,];
    var __VLS_190;
}
var __VLS_121;
/** @type {__VLS_StyleScopedClasses['page']} */ ;
/** @type {__VLS_StyleScopedClasses['page-header']} */ ;
/** @type {__VLS_StyleScopedClasses['sub-title']} */ ;
/** @type {__VLS_StyleScopedClasses['card']} */ ;
/** @type {__VLS_StyleScopedClasses['card-header']} */ ;
/** @type {__VLS_StyleScopedClasses['title']} */ ;
/** @type {__VLS_StyleScopedClasses['actions']} */ ;
/** @type {__VLS_StyleScopedClasses['time-row']} */ ;
/** @type {__VLS_StyleScopedClasses['time-sep']} */ ;
const __VLS_export = (await import('vue')).defineComponent({});
export default {};
